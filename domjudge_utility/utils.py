import json
import os


def object_to_json_string(obj):
    return json.dumps(obj, sort_keys=False, separators=(',', ':'), ensure_ascii=False)


def ensure_dir(_path: str):
    if not os.path.exists(_path):
        os.makedirs(_path)


def url_join(url, *args):
    url = url.rstrip('/')

    for arg in args:
        arg = arg.strip('/')
        url = "{}/{}".format(url, arg)

    return url
