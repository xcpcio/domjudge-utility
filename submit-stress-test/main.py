#! /usr/bin/env python3

import base64
import yaml
import logging
import os
import shutil

import requests
from requests_toolbelt import MultipartEncoder


def urlJoin(url, *args):
    url = url.rstrip('/')

    for arg in args:
        arg = arg.strip('/')
        url = "{}/{}".format(url, arg)

    return url


class Config:
    @staticmethod
    def getConfigWithDefaultCalue(config_dict, key, default_value):
        if key in config_dict.keys():
            return config_dict[key]

        return default_value

    def __init__(self, config_dict):
        self.base_url = self.getConfigWithDefaultCalue(
            config_dict, 'base_url', '')

        self.userpwd = self.getConfigWithDefaultCalue(
            config_dict, 'userpwd', '')

        self.cid = self.getConfigWithDefaultCalue(config_dict, 'cid', 0)

        self.api_version = self.getConfigWithDefaultCalue(
            config_dict, 'api_version', 'v4')

        self.total = self.getConfigWithDefaultCalue(config_dict, 'total', 1)

        self.test_data_path = self.getConfigWithDefaultCalue(
            config_dict, 'test_data_path', './test-data')


def loadConfig():
    global default_config

    config_path = './config.yaml'
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


def getLanguageByFileExtension(filepath):
    filename = os.path.split(filepath)[-1]
    file_extension = filename.split('.')[-1]

    if file_extension in ['c']:
        return 'c'

    if file_extension in ['cpp', 'cc', 'cxx', 'c++']:
        return 'cpp'

    if file_extension in ['java']:
        return 'java'

    if file_extension in ['py', 'py3']:
        return 'py3'

    return 'unknown'


def submit(pid, filepath):
    url = urlJoin(base_url, str(default_config.cid), 'submissions', '/')

    language = getLanguageByFileExtension(filepath)

    if language == 'unknown':
        logger.error("unknown language, filepath:{}".format(filepath))
        return

    with open(filepath, 'rb') as f:
        payload = {
            'problem': str(pid),
            'language': getLanguageByFileExtension(filepath),
            'code[]': (filepath, f.read(), 'application/octet-stream'),
        }

        m = MultipartEncoder(fields=payload)

        headers['Content-Type'] = m.content_type

        res = requests.post(url=url, headers=headers, data=m)

        if res.status_code != 200:
            logger.error("submit faield, filepath:{}, status_code:{}".format(
                filepath, res.status_code))

    pass


def stress():
    for dir in os.listdir(default_config.test_data_path):
        for file in os.listdir(os.path.join(default_config.test_data_path, dir)):
            submit(int(dir), os.path.join(
                default_config.test_data_path, dir, file))


def main():
    loadConfig()
    initLogging()

    global headers, base_url

    headers = {'Authorization': 'Basic ' +
               base64.encodebytes(default_config.userpwd.encode('utf-8')).decode('utf-8').strip(), 'Connection': 'close'}

    base_url = urlJoin(default_config.base_url, 'api',
                       default_config.api_version, 'contests')

    for i in range(default_config.total):
        logger.info(
            "start a new round of stress test, round number:{}".format(i))

        stress()


if __name__ == '__main__':
    main()
