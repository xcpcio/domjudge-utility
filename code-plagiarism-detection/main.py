#! /usr/bin/env python3

import os
import yaml
import logging
import base64
import json
import shutil


class Config:
    @staticmethod
    def getConfigWithDefaultCalue(config_dict, key, default_value):
        if key in config_dict.keys():
            return config_dict[key]

        return default_value

    def __init__(self, config_dict):
        self.base_api_file_path = self.getConfigWithDefaultCalue(
            config_dict, "base_api_file_path", "./domjudge-api")

        self.saved_dir = self.getConfigWithDefaultCalue(
            config_dict, 'saved_dir', './data')


def loadConfig():
    global default_config

    config_path = "./config.yaml"
    with open(config_path, 'r') as f:
        default_config = Config(yaml.load(f, Loader=yaml.FullLoader))


def initLogging():
    global logger

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)

    logger.addHandler(consoleHandler)


def outputToFile(filepath, data, if_not_exists=False):
    dir_name = os.path.join(default_config.saved_dir, filepath)

    if if_not_exists and os.path.exists(dir_name):
        return

    with open(dir_name, 'w', encoding='utf-8') as f:
        f.write(data)


def json_input(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def ensureDir(_path):
    if not os.path.exists(_path):
        os.makedirs(_path)


def getAPI(endpoint):
    return json_input(os.path.join(default_config.base_api_file_path, endpoint) + ".json")


def getSourceCode(submission_id):
    source_code_obj = json_input(os.path.join(default_config.base_api_file_path,
                                              'submissions', str(submission_id), 'source-code.json'))[0]

    source = source_code_obj['source']

    # Since the file encoding of the code depends on the file encoding when uploading.
    # So we need to try a variety of encoding decoding.
    # https://github.com/DOMjudge/domjudge/issues/1394#issuecomment-998738419
    for encoding_format in ['gb2312', 'utf-8']:
        try:
            return base64.b64decode(source).decode(encoding_format)
        except Exception as e:
            pass

    logger.error(
        "base64 decode failed. [submission_id={}, filename={}]".format(submission_id, source_code_obj['filename']))

    return ""


def getSuffixByLanguage(language_id):
    if language_id in ['c']:
        return '.cpp'

    if language_id in ['cpp']:
        return '.cpp'

    if language_id in ['java']:
        return '.java'

    if language_id in ['py', 'py3']:
        return '.py'


def convertSourceCode():
    for submission in submissions:
        submission_id = submission['id']
        language_id = submission['language_id']

        outputToFile(str(submission_id) + getSuffixByLanguage(language_id),
                     getSourceCode(submission_id))


def main():
    loadConfig()
    initLogging()

    global submissions

    submissions = getAPI('submissions')

    if os.path.exists(default_config.saved_dir):
        shutil.rmtree(default_config.saved_dir)

    ensureDir(default_config.saved_dir)

    convertSourceCode()


if __name__ == '__main__':
    main()
