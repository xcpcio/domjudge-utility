#! /usr/bin/env python3

import yaml
import time
import json


from domjudge_utility import Dump, DumpConfig

import requests


class Config:
    def __init__(self, base_url: str, userpwd: str, cid: str, xcpcio_token: str):
        self.base_url = base_url
        self.userpwd = userpwd
        self.cid = cid
        self.xcpcio_token = xcpcio_token


def load_config():
    config_path = './config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        return config


def dump(d: Dump, endpoint, filename, extra_files):
    content = d.request_json(endpoint)
    extra_files[filename] = content

    return content


def upload_all(c: Config, d: Dump):
    extra_files = {}

    contest = dump(d, '', 'contest.json', extra_files)
    awards = dump(d, 'awards', 'awards.json', extra_files)
    scoreboard = dump(d, 'scoreboard', 'scoreboard.json', extra_files)

    groups = dump(d, 'groups', 'groups.json', extra_files)
    judgements = dump(d, 'judgements', 'judgements.json', extra_files)
    judgement_types = dump(d, 'judgement-types',
                           'judgement-types.json', extra_files)
    languages = dump(d, 'languages', 'languages.json', extra_files)
    organizations = dump(d, 'organizations', 'organizations.json', extra_files)
    problems = dump(d, 'problems', 'problems.json', extra_files)
    teams = dump(d, 'teams', 'teams.json', extra_files)
    submissions = dump(d, 'submissions', 'submissions.json', extra_files)

    url = "https://board-admin.xcpcio.com/upload-board-data"

    payload = {
        "token": c.xcpcio_token,
        "extra_files": extra_files,
    }

    headers = {
        "content-type": "application/json",
    }

    resp = requests.post(url, json=payload, headers=headers)

    total_size = len(json.dumps(payload))

    if resp.status_code == 200:
        d.logger.info("upload successful. [resp={}] [size={}]".format(
            resp.content, total_size))
    else:
        d.logger.error("upload failed. [status_code={}] [resp={}] [size={}]".format(
            resp.status_code, resp.text, total_size))


def main():
    config_obj = load_config()
    c = Config(**config_obj)

    d_config = DumpConfig(config_obj)
    d = Dump(d_config)
    d.init_logging()

    while True:
        d.logger.info("upload starter")

        try:
            upload_all(c, d)
        except Exception as e:
            d.logger.error("upload failed. [err={}]".format(e))

        d.logger.info("sleeping...")
        time.sleep(5)


if __name__ == '__main__':
    main()
