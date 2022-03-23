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


bcolors = {
    'INFO':  '\033[94m',  # OKBLUE
    'DEBUG':  '\033[96m',  # OKCYAN
    'WARNING': '\033[93m',  # WARNING
    'ERROR': '\033[91m',  # FAIL
    'CRITICAL': '\033[0m',   # ENDC
}

_config = Config('scraper.ini')

with open('i18n/en-us.json', 'r') as raw_json_file:
    translation_json = json.load(raw_json_file)
    raw_json_file.close()


def log(level: int, message: str, data=None):
    logtofile(level, message, data)

    config_log_level = _config.get('application.LogLevel', 'error', toUpper)
    log_level = logging._nameToLevel[config_log_level]
    level_name = logging.getLevelName(level)

    if log_level > level:
        return

    print(f'{bcolors[level_name]}{level_name}: {message}\r')


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
        f'[{datetime.now().strftime("%m/%d/%Y|%H:%M:%S")}|{logging.getLevelName(level)}]: {message}\n')


def should_ignore_file(file: str) -> bool:
    try:
        file_extension = file.split('.')[1]
    except IndexError:
        log(logging.WARNING, f'file without extension: {file}')
        return True

    if _config.get_list('filesystem.SearchedFileExtensions').count(file_extension) <= 0:
        log(logging.DEBUG,
            f'file: {file} extension not allowed: {file_extension}')
        return True

    for ignored in _config.get_list('filesystem.IgnoreFilePatterns'):
        # log(logging.ERROR, f'{file}, {ignored}')
        # return

        match = re.search(ignored, file)
        if match:
            log(logging.DEBUG,
                f'file: {file} disallowed pattern {match.string}')
            return True

    return False


def should_ignore_folder(path: str) -> bool:
    for ignored in _config.get_list('filesystem.IgnoreFolderPatterns'):
        match = re.search(ignored, path)
        if match:
            log(logging.DEBUG,
                f'path: {path} matched disallowed pattern {match.string}')
            return True

    return False


def config_option(fullname: str, default=None, format=None):
    config = configparser.ConfigParser()
    section, option = fullname.split('.')
    config.read('scraper.ini')

    data = config.get(section=section, option=option, fallback=default)

    if not format:
        return data

    return format(data)


def load_config(config_file: str = None) -> None:

    config = configparser.ConfigParser()
    config.read(config_file or 'scraper.ini')

    config_delimiter = config.get('application', 'ConfigDelimiter')

    target_folders = config.get(
        section='filesystem',
        option='SearchedFolders'
    ).split(config_delimiter)

    target_extensions = config.get(
        section='filesystem',
        option='SearchedFileExtensions'
    ).split(config_delimiter)

    ignore_folder_patterns = config.get(
        section='filesystem',
        option='IgnoreFolderPatterns'
    ).split(config_delimiter)

    ignore_file_patterns = config.get(
        section='filesystem',
        option='IgnoreFilePatterns'
    ).split(config_delimiter)


def main():
    for directory in _config.get_list('filesystem.SearchedFolders'):
        log(logging.DEBUG, f'walking dir: {directory}')
        for root, dirs, files in os.walk(top=directory):
            log(logging.DEBUG, f'inside dir: {root}')
            path = root.split(os.sep)

            if should_ignore_folder(root):
                log(logging.INFO, f'skipping folder: {root}')
                continue

            for file in files:
                if should_ignore_file(file):
                    log(logging.INFO, f'skipping file: {root}/{file}')
                    continue

                with open(f'{root}/{file}') as target_file:
                    for translation_ref in translation_json.keys():
                        if translation_ref in target_file.read():
                            log(logging.INFO,
                                f'found {translation_ref} in {root}/{file}')
                            del translation_json[translation_ref]
        # print(file)

    # print(translation_json)
    return

    output = os.walk('src')

    for root, dirs, files in output:
        print({'root': root, 'directory': dirs, 'files': files})

    return
    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk("."):
        print({'root': root, 'directory': dirs, 'files': files})

        # path = root.split(os.sep)
        # print path
        # if excluded_folders.count(os.path.basename(root).lower()) > 0:
        #     continue
        print(os.path.basename(root))
        # print((len(path) - 1) * '---', os.path.basename(root))
        for file in files:
            continue
            print(len(path) * '---', file)


if __name__ == '__main__':
    main()
