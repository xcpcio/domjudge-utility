import os
import logging
import base64
import json
import math
import glob
import shutil
import time

import grequests
import requests

from . import utils
from .dump_config import DumpConfig


class Dump:
    def __init__(self, config: DumpConfig = None):
        if config is None:
            config = DumpConfig({})

        self.config = config

        self.headers = {
            "Authorization": 'Basic ' +
            base64.encodebytes(self.config.userpwd.encode(
                'utf-8')).decode('utf-8').strip(),
            "Connection": "close",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        }

        self.api_url = utils.url_join(
            self.config.base_url, "api", self.config.api_version, "contests")

        self.sub_dir_path = "domjudge"
        self.api_path_name = "api"
        self.submissions_path_name = 'submissions'
        self.images_path_name = 'images'

        self.api_dir = os.path.join(self.config.saved_dir,
                                    self.sub_dir_path, self.api_path_name)
        self.submissions_dir = os.path.join(
            self.config.saved_dir, self.sub_dir_path, self.submissions_path_name)
        self.images_dir = os.path.join(self.config.saved_dir,
                                       self.sub_dir_path, self.images_path_name)

        self.contest = None
        self.awards = None
        self.scoreboard = None
        self.groups = None
        self.judgements = None
        self.judgement_types = None
        self.languages = None
        self.organizations = None
        self.problems = None
        self.teams = None
        self.submissions = None
        self.clarifications = None
        self.event_feed = None

        self.problems_dict = None
        self.groups_dict = None
        self.teams_dict = None

        self.logger = None

    def output_to_file(self, filepath: str, data: str, if_not_exists=False):
        dir_name = os.path.join(self.config.saved_dir, filepath)

        if if_not_exists and os.path.exists(dir_name):
            return

        with open(dir_name, 'w', encoding='utf-8') as f:
            f.write(data)

    def init_logging(self):
        if self.logger is not None:
            return

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(formatter)

        self.logger.addHandler(consoleHandler)

    def send_request(self, url, params={}):
        res = requests.get(url=url, headers=self.headers, params=params)

        if res.status_code != 200:
            self.logger.error('An error occurred during request GET {}, errcode:{}'.format(
                url, res.status_code))
            exit()

        return res

    def request_json(self, endpoint, params={}):
        if self.config.base_file_path == '':
            url = utils.url_join(self.api_url, str(self.config.cid))

            if len(endpoint) > 0:
                url = utils.url_join(url, endpoint)

            self.logger.info('GET {}'.format(url))

            resp = self.send_request(url, params)

            content_type = resp.headers.get("Content-Type")

            if "charset" in content_type:
                charset = content_type.split("charset=")[1]
                content = resp.content.decode(charset)
            else:
                content = resp.content.decode()

            return content
        else:
            file_path = os.path.join(self.config.base_file_path, "domjudge", "api", endpoint)
            self.logger.info('GET {}'.format(file_path))
            with open(file_path, 'r') as f:
                return f.read()

    def image_download(self, img_url: str, dist: str):
        self.logger.info(
            "download image. [img_url=%s] [dist=%s]", img_url, dist)

        utils.ensure_dir(os.path.split(dist)[0])
        res = self.send_request(img_url)

        with open(dist, 'wb') as f:
            f.write(res.content)

    def request_json_and_save(self, endpoint, filename, params={}):
        content = self.request_json(
            endpoint if self.config.base_file_path == '' else filename, params=params)

        if self.config.exported_data.domjudge_api:
            utils.ensure_dir(self.api_dir)
            self.output_to_file(os.path.join(
                self.sub_dir_path, self.api_path_name, filename), content)

        try:
            if filename.endswith(".json"):
                return json.loads(content)
            else:
                return content
        except Exception as err:
            self.logger.error(err)
            return content

    def add_verdict(self, submissions, judgements):
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

    def get_seconds(self, t):
        h, m, s = t.strip().split(":")
        return math.floor(int(h) * 3600 + int(m) * 60 + math.floor(float(s)))

    def get_submission_timestamp(self, t):
        h, m, s = t.strip().split(":")
        timestamp = int(h) * 3600 + int(m) * 60

        if self.config.score_in_seconds:
            timestamp += math.floor(float(s))

        return timestamp

    def is_observers(self, team):
        for group_id in team['group_ids']:
            if self.groups_dict[group_id]['name'] == 'Observers':
                return True

        return False

    def dump_domjudge_api(self):
        self.contest = self.request_json_and_save('', 'contest.json')
        self.awards = self.request_json_and_save('awards', 'awards.json')
        self.scoreboard = self.request_json_and_save(
            'scoreboard', 'scoreboard.json')

        self.groups = self.request_json_and_save('groups', 'groups.json')
        self.judgements = self.request_json_and_save(
            'judgements', 'judgements.json')
        self.judgement_types = self.request_json_and_save(
            'judgement-types', 'judgement-types.json')
        self.languages = self.request_json_and_save(
            'languages', 'languages.json')
        self.organizations = self.request_json_and_save(
            'organizations', 'organizations.json')
        self.problems = self.request_json_and_save('problems', 'problems.json')
        self.teams = self.request_json_and_save('teams', 'teams.json')
        self.submissions = self.request_json_and_save(
            'submissions', 'submissions.json')

        self.clarifications = self.request_json_and_save(
            'clarifications', 'clarifications.json')

        if self.config.exported_data.event_feed:
            self.event_feed = self.request_json_and_save(
                'event-feed', 'event-feed.ndjson', {'stream': False, 'strict': True})

    def dump_runs(self):
        if not self.config.exported_data.runs:
            return

        if self.config.base_file_path != '':
            for filepath in glob.glob('{}/runs.*.json'.format(self.config.base_file_path)):
                filename = os.path.split(filepath)[-1]

                src = os.path.join(self.config.base_file_path, filename)
                dst = os.path.join(
                    self.config.saved_dir, self.sub_dir_path, filename)

                self.logger.info("%s,%s" % (src, dst))

                shutil.copyfile(src, dst)

            return

        if self.config.base_url != '':
            runs = self.request_json_and_save(
                'runs?limit=10000', 'runs.1.json')

            i = 2
            saved_filename = ''

            while len(runs) != 0:
                endpoint = 'runs?limit=10000&first_id={}'.format(
                    str(int(runs[-1]['id'])+1))

                saved_filename = 'runs.{}.json'.format(str(i))

                runs = self.request_json_and_save(endpoint, saved_filename)
                i = i + 1

            # Obviously, there will be an empty JSON file
            os.remove(os.path.join(self.config.saved_dir,
                                   self.sub_dir_path, self.api_path_name, saved_filename))

    def download_source_code(self, submission_id_list):
        err_list = []

        def exception_handler(request, exception):
            self.logger.error('An error occurred during request GET {}, exception:{}'.format(
                request.url, exception))

            err_list.append(request)

        reqs = []

        for submission_id in submission_id_list:
            url_prefix = utils.url_join(self.api_url, str(self.config.cid),
                                        'submissions', str(submission_id))
            reqs.append(grequests.get(url=utils.url_join(
                url_prefix, 'files'), headers=self.headers))
            reqs.append(grequests.get(url=utils.url_join(
                url_prefix, 'source-code'), headers=self.headers))

        res_list = grequests.map(reqs, exception_handler=exception_handler)

        if len(err_list) > 0:
            return False

        for i in range(0, len(res_list), 2):
            submission_id = submission_id_list[i // 2]

            res_files = res_list[i]
            res_source_code = res_list[i + 1]

            with open(os.path.join(self.submissions_dir, str(submission_id), 'files.zip'), 'wb') as f:
                f.write(res_files.content)

            with open(os.path.join(self.submissions_dir, str(submission_id), 'source-code.json'), 'w') as f:
                f.write(res_source_code.content.decode('unicode-escape'))

        return True

    def dump_source_code(self):
        if not self.config.exported_data.source_code:
            return

        if self.config.base_file_path != '':
            path_name = os.path.join(
                self.config.base_file_path, self.submissions_path_name)
            if os.path.exists(path_name):
                shutil.copytree(path_name, self.submissions_dir)

            return

        if self.config.base_url != '':
            total = len(self.submissions)
            i = 0

            utils.ensure_dir(self.submissions_dir)

            submission_id_list = []

            for submission in self.submissions:
                submission_id = submission['id']
                submission_id_list.append(submission_id)

                utils.ensure_dir(os.path.join(
                    self.submissions_dir, submission_id))

                i = i + 1
                if i % 100 == 0 or i == total:
                    while not self.download_source_code(submission_id_list):
                        time.sleep(1)
                        self.logger.info("retrying")

                    submission_id_list.clear()

                    self.logger.info(
                        'Submissions {}/{}'.format(str(i), str(total)))

    def dump_images(self):
        if not self.config.exported_data.images:
            return

        # contest
        if "banner" in self.contest.keys():
            for b in self.contest["banner"]:
                href = b["href"]
                self.image_download(utils.url_join(self.config.base_url, "api",
                                                   self.config.api_version, href), os.path.join(self.images_dir, href))

        # organization
        for o in self.organizations:
            if "logo" in o.keys():
                for logo in o["logo"]:
                    href = logo["href"]
                    self.image_download(utils.url_join(self.config.base_url, "api",
                                                       self.config.api_version, href), os.path.join(self.images_dir, href))

        # team
        for t in self.teams:
            if "photo" in t.keys():
                for photo in t["photo"]:
                    href = photo["href"]
                    self.image_download(utils.url_join(self.config.base_url, "api",
                                                       self.config.api_version, href), os.path.join(self.images_dir, href))

    def get_ghost_dat_data(self, contest, teams_dict, submissions, problems_dict):
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

        if self.config.add_dummy_russian_team:
            team_nums += need_dummy_teams

        dat_data = ''

        dat_data += '@contest "{}"\n'.format(contest['formal_name'])
        dat_data += '@contlen {}\n'.format(
            int(self.get_seconds(contest['duration']) // 60))
        dat_data += '@problems {}\n'.format(len(problems_dict))
        dat_data += '@teams {}\n'.format(team_nums)
        dat_data += '@submissions {}\n'.format(len(submissions))

        for problem in problems_dict.values():
            label = problem['label']
            name = problem['name']

            dat_data += '@p {},{},20,0\n'.format(label, name)

        team_index = 1
        team_index_dict = {}

        for id, team in teams_dict.items():
            affiliation = team['affiliation']
            name = team['name']

            team_id = team_index
            team_index += 1
            team_index_dict[id] = team_id

            dat_data += '@t {},0,1,{} {}{}\n'.format(
                team_id, affiliation, '*' if self.is_observers(team) else '', name)

        if self.config.add_dummy_russian_team:
            for i in range(need_dummy_teams):
                dat_data += '@t {},0,1,Пополнить команду\n'.format(team_index)
                team_index += 1

        teams_submit_index_dict = {}
        for submission in submissions:
            team_id = team_index_dict[submission['team_id']]
            problem_label = problems_dict[submission['problem_id']]['label']

            if team_id in teams_submit_index_dict.keys():
                teams_submit_index_dict[team_id] += 1
            else:
                teams_submit_index_dict[team_id] = 1

            team_submit_index = teams_submit_index_dict[team_id]
            timestamp = self.get_submission_timestamp(
                submission['contest_time'])

            verdict = verdict_mapping[submission['verdict']]

            dat_data += '@s {},{},{},{},{}\n'.format(
                team_id, problem_label, team_submit_index, timestamp, verdict)

        self.output_to_file('contest.dat', dat_data)

    def get_resolver_data(self, contest, teams, submissions, problems_dict):
        resolver_data = {}
        resolver_data["contest_name"] = contest["formal_name"]
        resolver_data["problem_count"] = len(problems_dict)
        resolver_data["frozen_seconds"] = self.get_seconds(
            contest["duration"]) - self.get_seconds(contest["scoreboard_freeze_duration"])

        users = {}
        solutions = {}

        for team in teams:
            item = {}
            item['name'] = team['name']
            item['college'] = team['affiliation']
            item['is_exclude'] = self.is_observers(team)

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
            item['submitted_seconds'] = self.get_submission_timestamp(
                submission['contest_time'])

            # TOO LATE submission
            if item['submitted_seconds'] > self.get_seconds(contest["duration"]):
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

        self.output_to_file(
            'resolver.json', utils.object_to_json_string(resolver_data))

    def get_excel_data(self, contest, scoreboard, problems_dict, teams_dict):
        import xlwt

        def get_title_style():
            font = xlwt.Font()
            font.name = u'Arial Unicode MS'
            font.bold = True
            font.height = 420

            alignment = xlwt.Alignment()
            alignment.horz = 0x02
            alignment.vert = 0x01

            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1

            style = xlwt.XFStyle()
            style.font = font
            style.alignment = alignment
            style.borders = borders

            return style

        def get_content_style():
            font = xlwt.Font()
            font.name = u'Arial Unicode MS'
            font.bold = True
            font.height = 20 * 11

            alignment = xlwt.Alignment()
            alignment.horz = 0x02
            alignment.vert = 0x01
            alignment.wrap = 1

            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1

            style = xlwt.XFStyle()
            style.font = font
            style.alignment = alignment
            style.borders = borders

            return style

        file_path = os.path.join(self.config.saved_dir,
                                 '{}.xls'.format(contest['formal_name'].replace(' ', '-')))

        sheet_name = "scoreboard"
        title = contest['formal_name']

        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet(sheet_name)

        title_style = get_title_style()
        content_style = get_content_style()

        row = [['Rank', 'Affiliation', 'Name', 'Solved', 'Penalty']]

        for p in self.problems:
            row[0].append(p['label'])

        for item in scoreboard['rows']:
            team = teams_dict[item['team_id']]

            res = [item['rank'], team['affiliation'], team['name'],
                   item['score']['num_solved'], item['score']['total_time']]

            for p in item['problems']:
                num_judged = p['num_judged']

                if num_judged == 0:
                    res.append('-')
                elif p['solved'] == True:
                    res.append('+{}({})'.format(p['num_judged'], p['time']))
                else:
                    res.append('-{}'.format(p['num_judged']))

            row.append(res)

        row_num = len(row[0])
        row_max_len = [0] * row_num

        sheet.write_merge(0, 0, 0, row_num - 1, title, title_style)

        for i in range(len(row)):
            for j in range(len(row[i])):
                row_max_len[j] = max(row_max_len[j], len(
                    str(row[i][j]).encode('gb18030')))

        for i in range(len(row)):
            for j in range(len(row[i])):
                sheet.write(i + 1, j, row[i][j], content_style)

        # Set adaptive column width
        for i in range(0, row_num):
            # 256 * ${words_length}
            # In order not to appear particularly compact
            # increase the width of two characters
            sheet.col(i).width = 256 * (row_max_len[i] + 4)

        workbook.save(file_path)

    def process_domjudge_raw_data(self):
        self.problems_dict = {}
        for problem in self.problems:
            self.problems_dict[problem['id']] = problem

        self.groups_dict = {}
        for group in self.groups:
            self.groups_dict[group['id']] = group

        self.teams_dict = {}
        for team in self.teams:
            self.teams_dict[team['id']] = team

        self.add_verdict(self.submissions, self.judgements)

    def dump_3rd_data(self):
        ex = self.config.exported_data
        if not any([ex.ghost_dat_data, ex.resolver_data, ex.scoreboard_excel_data]):
            return

        self.process_domjudge_raw_data()

        if self.config.exported_data.ghost_dat_data:
            self.get_ghost_dat_data(
                self.contest, self.teams_dict, self.submissions, self.problems_dict)

        if self.config.exported_data.resolver_data:
            self.get_resolver_data(self.contest, self.teams, self.submissions,
                                   self.problems_dict)

        if self.config.exported_data.scoreboard_excel_data:
            self.get_excel_data(self.contest, self.scoreboard,
                                self.problems_dict, self.teams_dict)

    def dump(self):
        if os.path.exists(self.config.saved_dir):
            shutil.rmtree(self.config.saved_dir)

        utils.ensure_dir(self.config.saved_dir)

        self.dump_domjudge_api()
        self.dump_runs()
        self.dump_source_code()
        self.dump_images()
        self.dump_3rd_data()

    def load_domjudge_api(self):
        self.config.exported_data.domjudge_api = False

        self.init_logging()
        self.dump_domjudge_api()
        self.process_domjudge_raw_data()
