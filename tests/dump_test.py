import os
import json

from domjudge_utility import Dump, DumpConfig

current_file_path = os.path.abspath(__file__)
current_dir_path = os.path.dirname(current_file_path)


def test_dump_9th_ccpc_guilin(snapshot):
    test_prefix = "9th_ccpc_guilin"

    fetch_uri = os.path.join(current_dir_path, "test_data", test_prefix)

    c = DumpConfig()
    c.base_file_path = fetch_uri

    d = Dump(c)
    d.load_domjudge_api()

    snapshot.assert_match(json.dumps(d.contest), "contest")
    snapshot.assert_match(json.dumps(d.awards), "awards")
    snapshot.assert_match(json.dumps(d.scoreboard), "scoreboard")
    snapshot.assert_match(json.dumps(d.groups), "groups")
    snapshot.assert_match(json.dumps(d.judgements), "judgements")
    snapshot.assert_match(json.dumps(d.judgement_types), "judgement_types")
    snapshot.assert_match(json.dumps(d.languages), "languages")
    snapshot.assert_match(json.dumps(d.organizations), "organizations")
    snapshot.assert_match(json.dumps(d.problems), "problems")
    snapshot.assert_match(json.dumps(d.teams), "teams")
    snapshot.assert_match(json.dumps(d.submissions), "submissions")
