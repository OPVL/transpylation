import configparser
from datetime import datetime
import json
import logging
import math
import os
import re

logging.SUCCESS = logging.CRITICAL + 10
logging.addLevelName(logging.SUCCESS, 'SUCCESS')


def _filename_from_file() -> str:
    return __file__.split('/')[-1].split('.')[0]


def toUpper(string: str):
    return string.upper()


def human_size(size_bytes: int):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    power = math.pow(1024, i)
    size = round(size_bytes / power, 2)
    return f"{size} {size_name[i]}"


def alphabetise_dict(input: dict) -> dict:
    return dict(sorted(input.items(), key=lambda x: x[0].lower()))


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

    def get_bool(self, full_option: str, default=None):
        section, option = full_option.split('.')

        data = self.config.getboolean(
            section=section,
            option=option,
            fallback=default
        )

        return data

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


def level_to_colour(level: int) -> str:
    if level < 30:
        return ''

    if level == logging.WARN:
        return console_colours.get('yellow')

    if level == logging.SUCCESS:
        return console_colours.get('green')

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
    logfile.write(f'[{datetime.now().strftime("%m/%d/%Y|%H:%M:%S")}|{logging.getLevelName(level)}]: {message} {data or ""}\n')


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
        log(f'file without extension: {file}')
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


def is_file_large(file: str, root: str):
    size = os.path.getsize(f'{root}/{file}')
    config_size = _config.get('filesystem.SizeThreshold', 10240, int)

    if size > config_size:
        log(f'{file} size: {human_size(size)} larger than threshold {human_size(config_size)}')
        return True

    return False


def search_file(searching_for: str, file: str, root: str) -> bool:
    target_file = open(f'{root}/{file}', 'r')
    found = searching_for in target_file.read()

    if found:
        log(f'found {searching_for} in {file}', level=logging.INFO)
        return True

    return False


def search_file_by_line(searching_for: str, file: str, root: str) -> bool:
    linecount = 1
    target_file = open(f'{root}/{file}', 'r')

    for line in target_file.readlines():
        if searching_for in line:
            log(f'found {searching_for} in {file} on line {linecount}', level=logging.INFO)
            return True
        linecount += 1
    return False


def display_results(results: list, tranlation_filename: str):
    if _config.get_bool('output.WriteToFile'):
        outfile = open(f"{tranlation_filename.split('.')[0]}-{_config.get('output.OutFile', 'unused')}.json", 'w')
        json.dump(results, outfile)
        outfile.close()

    if _config.get_bool('output.WriteToConsole'):
        if len(results) < 1:
            return

        log(f'found {len(results)} unused translations in {tranlation_filename}',
            level=logging.SUCCESS, data=results)


def load_translation(translation_file: str) -> dict:
    i18n = open(translation_file, 'r')
    translation_json = json.load(i18n)
    i18n.close()

    return translation_json


def search_for_translations(translation_file: str) -> dict:
    found = {}
    translation_json = load_translation(translation_file)

    for directory in _config.get_list('filesystem.SearchedFolders'):
        log(f'walking dir: {directory}')
        for root, dirs, files in os.walk(top=directory):
            log(f'inside dir: {root}')

            if should_ignore_folder(root):
                log(f'skipping folder: {root}')
                continue

            for file in files:
                if should_ignore_file(file):
                    log(f'skipping file: {root}/{file}')
                    continue

                large_file = is_file_large(file, root)

                for translation_ref in translation_json.keys():
                    if found.get(translation_ref):
                        log(f'skipping found translation: {translation_ref}')
                        continue

                    if large_file:
                        success = search_file(translation_ref, file, root)
                    else:
                        success = search_file_by_line(translation_ref, file, root)

                    if success:
                        found[translation_ref] = translation_json[translation_ref]
    diff = list(set(translation_json) - set(found))
    display_results(diff, translation_file)
    return found


def is_valid(filename: str) -> bool:
    return filename.endswith('.json') and not _config.get('output.OutFile') in filename


def update_translation_file(file: str, update: dict):
    log(f'updating translation file {file}')
    if _config.get_bool('output.MakeBackups'):
        log(f'making backup {file}.bak')
        t_file = open(file, 'r')
        contents = json.load(t_file)
        t_file.close()

        backup = open(f'{file}.bak', 'w')
        json.dump(alphabetise_dict(contents), backup)
        backup.close()

    out_trans_file = open(file, 'w')
    json.dump(alphabetise_dict(update), out_trans_file)
    out_trans_file.close()


def main():

    if _config.get_bool('application.UseDirectory'):
        for root, dirs, files in os.walk(_config.get('application.TranslationDir')):
            translations = list(
                map(
                    lambda file: f'{_config.get("application.TranslationDir")}/{file}',
                    filter(is_valid, files))
            )
    else:
        translations = [_config.get('application.TranslationFile')]

    for translation_file in translations:
        log(f'searching file: {translation_file}', level=logging.INFO)
        result = search_for_translations(translation_file)
        if _config.get_bool('output.UpdateTranslation'):
            update_translation_file(translation_file, result)


if __name__ == '__main__':
    main()
