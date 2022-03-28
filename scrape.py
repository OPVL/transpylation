import configparser
from datetime import datetime
import json
import logging
import os
import re


def _filename_from_file() -> str:
    return __file__.split('/')[-1].split('.')[0]


def toUpper(string: str):
    return string.upper()


class Config():
    def __init__(self, config_file=None) -> None:
        self.config = configparser.ConfigParser()
        self._open_config(config_file)

    def _open_config(self, config_file) -> str:
        file = config_file or f"{_filename_from_file()}.ini"
        self.config.read(file)

    @property
    def config_delimiter(self) -> str:
        return self.get('application.ConfigDelimiter', ',')

    def _to_list(self, data: str) -> list:
        return data.split(self.config_delimiter)

    def get(self, full_option: str, default=None, format=None):
        section, option = full_option.split('.')

        data = self.config.get(
            section=section,
            option=option,
            fallback=default
        )

        return data if not format else format(data)

    def get_list(self, full_option: str, default=None) -> list:
        section, option = full_option.split('.')

        data = self.config.get(
            section=section,
            option=option,
            fallback=default
        )

        return self._to_list(data)


console_colours = {
    'purple': '\033[95m',
    'blue': '\033[94m',
    'cyan': '\033[96m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'red': '\033[91m',
    'bold': '\033[1m',
    'underline': '\033[4m',
    'endcolour': '\033[0m',
}

_config = Config('scraper.ini')

with open('i18n/en-us.json', 'r') as raw_json_file:
    translation_json = json.load(raw_json_file)
    raw_json_file.close()


def level_to_colour(level: int) -> str:
    if level < 30:
        return ''

    if level == logging.WARN:
        return console_colours.get('yellow')

    if level >= logging.ERROR:
        return console_colours.get('red')


def logtofile(level: int, message: str, data=None):
    if not _config.get('application.Debug', bool):
        return

    config_file_level = _config.get(
        'application.LogFileLevel', 'warning', toUpper)
    file_level = logging._nameToLevel[config_file_level]

    if file_level > level:
        return

    logfile = open(_config.get('application.LogFile',
                   f'{_filename_from_file()}.log'), 'a')
    logfile.write(
        f'[{datetime.now().strftime("%m/%d/%Y|%H:%M:%S")}|{logging.getLevelName(level)}]: {message} {data}\n')


def log(message: str, level: int = None, data=None, colour: str = None):

    level = level or logging.DEBUG
    logtofile(message=message, level=level, data=data)

    config_log_level = _config.get('application.LogLevel', 'error', toUpper)
    log_level = logging._nameToLevel[config_log_level]
    level_name = logging.getLevelName(level)

    if log_level > level:
        return

    print(
        f"{console_colours.get(colour, None) or level_to_colour(level)}{level_name}: {message}{console_colours['endcolour']}\r")


def should_ignore_file(file: str) -> bool:
    try:
        file_extension = file.split('.')[1]
    except IndexError:
        log(f'file without extension: {file}', level=logging.WARNING)
        return True

    if _config.get_list('filesystem.SearchedFileExtensions').count(file_extension) <= 0:
        log(f'file: {file} extension not allowed: {file_extension}')
        return True

    for ignored in _config.get_list('filesystem.IgnoreFilePatterns'):
        match = re.search(ignored, file)
        if match:
            log(f'file: {file} disallowed pattern {match.string}')
            return True

    return False


def should_ignore_folder(path: str) -> bool:
    for ignored in _config.get_list('filesystem.IgnoreFolderPatterns'):
        match = re.search(ignored, path)
        if match:
            log(f'path: {path} matched disallowed pattern {match.string}')
            return True

    return False


def does_file_contain(searching_for, file, root):
    size = os.path.getsize(f'{root}/{file}')
    config_size = _config.get('filesystem.SizeThreshold', 1024, int)
    log(f'{file} size is {size}')

    if size > config_size:
        log(f'{file} size: {size} larger than threshold {config_size}')
        # return search_file_by_line(file, searching_for)

    target_file = open(f'{root}/{file}', 'r')

    found = searching_for in target_file.read()

    if found:
        log(f'found {searching_for} in {file}')
        return True

    return False


def search_file_by_line(file, search):
    return False


def main():

    found = {}
    for directory in _config.get_list('filesystem.SearchedFolders'):
        log(f'walking dir: {directory}')
        for root, dirs, files in os.walk(top=directory):
            log(f'inside dir: {root}')
            path = root.split(os.sep)

            if should_ignore_folder(root):
                log(f'skipping folder: {root}', level=logging.INFO)
                continue

            for file in files:
                if should_ignore_file(file):
                    log(f'skipping file: {root}/{file}', level=logging.INFO)
                    continue

                for translation_ref in translation_json.keys():
                    if found.get(translation_ref):
                        continue

                    if does_file_contain(translation_ref, file, root):
                        found[translation_ref] = translation_json[translation_ref]

    diff = list(set(translation_json) - set(found))
    log(f'found {len(diff)} unused translations',
        level=logging.INFO, data=diff)

    outfile = open('unused.json', 'w')
    outfile.write(json.dumps(diff))
    outfile.close()


if __name__ == '__main__':
    main()
