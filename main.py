#! /usr/bin/env python3

import base64
import os
import json
import time
import logging
import requests
import shutil
import math
import yaml


def objectToJSONString(obj):
    return json.dumps(obj, sort_keys=False, separators=(',', ':'), ensure_ascii=False)


def outputToFile(filename, data, if_not_exists=False):
    dir_name = os.path.join(default_config.saved_dir, filename)

    if if_not_exists and os.path.exists(dir_name):
        return

    with open(dir_name, 'w', encoding='utf-8') as f:
        f.write(data)


def ensureDir(_path):
    if not os.path.exists(_path):
        os.makedirs(_path)


def urlJoin(url, *args):
    url = url.rstrip('/')

    for arg in args:
        arg = arg.strip('/')
        url = "{}/{}".format(url, arg)

    return url


class Config:
    def getConfigWithDefaultCalue(self, config_dict, key, default_value):
        if key in config_dict.keys():
            return config_dict[key]

        return default_value

    def __init__(self, config_dict):
        self.base_file_path = self.getConfigWithDefaultCalue(
            config_dict, 'base_file_path', '')

        self.base_url = self.getConfigWithDefaultCalue(
            config_dict, 'base_url', '')

        self.userpwd = self.getConfigWithDefaultCalue(
            config_dict, 'userpwd', '')

        self.cid = self.getConfigWithDefaultCalue(config_dict, 'cid', 0)

        self.api_version = self.getConfigWithDefaultCalue(
            config_dict, 'api_version', 'v4')

        self.saved_dir = self.getConfigWithDefaultCalue(
            config_dict, 'saved_dir', './data')

        self.score_in_seconds = self.getConfigWithDefaultCalue(
            config_dict, 'score_in_seconds', False)

        self.add_dummy_russian_team = self.getConfigWithDefaultCalue(
            config_dict, 'add_dummy_russian_team', False)

        self.save_domjudge_api_to_file = self.getConfigWithDefaultCalue(
            config_dict, 'save_domjudge_api_to_file', True)


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


def requestJson(endpoint):
    if default_config.base_file_path == '':
        url = urlJoin(base_url, str(default_config.cid))

        if len(endpoint) > 0:
            url = urlJoin(url, endpoint)

        logger.info('GET {}'.format(url))
        res = requests.get(url=url, headers=headers)
        logger.info('Result Code: {}'.format(res.status_code))

        if res.status_code != 200:
            logger.error('An error occurred during request.')
            exit()

        return res.content.decode('unicode-escape')
    else:
        file_path = os.path.join(default_config.base_file_path, endpoint)
        logger.info('GET {}'.format(file_path))
        with open(file_path, 'r', encoding='unicode-escape') as f:
            return f.read()


def requestJsonAndSave(endpoint, filename):
    content = requestJson(
        endpoint if default_config.base_file_path == '' else filename)

    outputToFile(filename, content)

    return json.loads(content)


def getSeconds(t):
    h, m, s = t.strip().split(":")
    return math.floor(int(h) * 3600 + int(m) * 60 + math.floor(float(s)))


def getSubmissionTimestamp(t):
    h, m, s = t.strip().split(":")
    timestamp = int(h) * 3600 + int(m) * 60

    if default_config.score_in_seconds:
        timestamp += math.floot(float(s))

    return timestamp


def isObservers(team):
    for group_id in team['group_ids']:
        if groups_dict[group_id]['name'] == 'Observers':
            return True

    return False


def getResolverData(contest, teams, submissions, problems_dict):
    resolver_data = {}
    resolver_data["contest_name"] = contest["formal_name"]
    resolver_data["problem_count"] = len(problems_dict)
    resolver_data["frozen_seconds"] = getSeconds(
        contest["duration"]) - getSeconds(contest["scoreboard_freeze_duration"])

    users = {}
    solutions = {}

    for team in teams:
        item = {}
        item['name'] = team['name']
        item['college'] = team['affiliation']
        item['is_exclude'] = isObservers(team)

        users[team['id']] = item

    submission_index = 1
    for submission in submissions:
        id = submission['id']
        verdict = submission['verdict']

        if verdict != 'AC' and verdict != 'CE':
            verdict = 'WA'

        if verdict == 'CE':
            continue

        item = {}
        item['submitted_seconds'] = getSubmissionTimestamp(
            submission['contest_time'])

        # TOO LATE submission
        if item['submitted_seconds'] > getSeconds(contest["duration"]):
            continue

        item['user_id'] = submission['team_id']

        if item['user_id'] not in users.keys():
            continue

        # Count from 1
        item['problem_index'] = str(ord(
            problems_dict[submission['problem_id']]['label']) - ord('A') + 1)

        item['verdict'] = verdict

        solutions[submission_index] = item
        submission_index += 1

    resolver_data['solutions'] = solutions
    resolver_data['users'] = users

    outputToFile('resolver.json', objectToJSONString(resolver_data))


def getDATData(contest, teams_dict, submissions, problems_dict):
    verdict_mapping = {
        'CE': 'CE',
        'MLE': 'ML',
        'OLE': 'IL',
        'RTE': 'RT',
        'TLE': 'TL',
        'WA': 'WA',
        'PE': 'CE',
        'NO': 'WA',
        'AC': 'OK',
        'PD': 'PD',
    }

    team_nums = len(teams_dict)
    need_dummy_teams = team_nums

    if default_config.add_dummy_russian_team:
        team_nums += need_dummy_teams

    dat_data = ''

    dat_data += '@contest "{}"\n'.format(contest['formal_name'])
    dat_data += '@contlen {}\n'.format(
        int(getSeconds(contest['duration']) // 60))
    dat_data += '@problems {}\n'.format(len(problems_dict))
    dat_data += '@teams {}\n'.format(team_nums)
    dat_data += '@submissions {}\n'.format(len(submissions))

    for problem in problems_dict.values():
        label = problem['label']
        name = problem['name']

        dat_data += '@p {},{},20,0\n'.format(label, name)

    team_index = 1
    team_index_dict = {}

    if default_config.add_dummy_russian_team:
        for i in range(need_dummy_teams):
            dat_data += '@t {},0,1,Пополнить команду\n'.format(team_index)
            team_index += 1

    for id, team in teams_dict.items():
        affiliation = team['affiliation']
        name = team['name']

        team_id = team_index
        team_index += 1
        team_index_dict[id] = team_id

        dat_data += '@t {},0,1,{} {}{}\n'.format(
            team_id, affiliation, '*' if isObservers(team) else '', name)

    teams_submit_index_dict = {}
    for submission in submissions:
        team_id = team_index_dict[submission['team_id']]
        problem_label = problems_dict[submission['problem_id']]['label']

        if team_id in teams_submit_index_dict.keys():
            teams_submit_index_dict[team_id] += 1
        else:
            teams_submit_index_dict[team_id] = 1

        team_submit_index = teams_submit_index_dict[team_id]
        timestamp = getSubmissionTimestamp(submission['contest_time'])

        verdict = verdict_mapping[submission['verdict']]

        dat_data += '@s {},{},{},{},{}\n'.format(
            team_id, problem_label, team_submit_index, timestamp, verdict)

    outputToFile('contest.dat', dat_data)


def addVerdict(submissions, judgements):
    submissions_verdict = {}
    for judgement in judgements:
        id = judgement['submission_id']
        verdict = judgement['judgement_type_id']

        submissions_verdict[id] = verdict

    for submission in submissions:
        id = submission['id']

        # Pending
        if id not in submissions_verdict.keys():
            submission['verdict'] = 'PD'
        else:
            submission['verdict'] = submissions_verdict[id]


def export():
    global headers, base_url, submissions_dir
    global contest, awards, scoreboard, groups, judgements
    global judgement_types, languages, organizations, problems, teams, submissions
    global problems_dict, groups_dict, teams_dict

    loadConfig()
    initLogging()

    headers = {'Authorization': 'Basic ' +
               base64.encodebytes(default_config.userpwd.encode('utf-8')).decode('utf-8').strip()}

    base_url = urlJoin(default_config.base_url, 'api',
                       default_config.api_version, 'contests')

    submissions_dir = os.path.join(default_config.saved_dir, 'submissions')

    if os.path.exists(default_config.saved_dir):
        shutil.rmtree(default_config.saved_dir)

    ensureDir(default_config.saved_dir)

    contest = requestJsonAndSave('', 'contest.json')
    awards = requestJsonAndSave('awards', 'awards.json')
    scoreboard = requestJsonAndSave('scoreboard', 'scoreboard.json')
    # clarifications = requestJsonAndSave(
    #     'clarifications', 'clarifications.json')
    # event_feed =  requestJsonAndSave('event-feed', 'event-feed.json')
    groups = requestJsonAndSave('groups', 'groups.json')
    judgements = requestJsonAndSave('judgements', 'judgements.json')
    judgement_types = requestJsonAndSave(
        'judgement-types', 'judgement-types.json')
    languages = requestJsonAndSave('languages', 'languages.json')
    organizations = requestJsonAndSave('organizations', 'organizations.json')
    problems = requestJsonAndSave('problems', 'problems.json')
    teams = requestJsonAndSave('teams', 'teams.json')
    submissions = requestJsonAndSave('submissions', 'submissions.json')

    problems_dict = {}
    for problem in problems:
        problems_dict[problem['id']] = problem

    groups_dict = {}
    for group in groups:
        groups_dict[group['id']] = group

    teams_dict = {}
    for team in teams:
        teams_dict[team['id']] = team

    addVerdict(submissions, judgements)

    getResolverData(contest, teams, submissions,
                    problems_dict)
    getDATData(contest, teams_dict, submissions, problems_dict)


if __name__ == '__main__':
    export()
