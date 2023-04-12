import os
import requests

import config
from logger import init_logger

global_config = config.load_config()
logger = init_logger()


def fetch_html(fetch_item: config.FetchItem):
    url = global_config.url + fetch_item.url_suffix
    logger.info("fetch html. [url={}]".format(url))

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    }

    resp = requests.get(url, timeout=5, headers=headers)

    saved_dir = os.path.join(global_config.saved_dir, fetch_item.dir_name)
    if not os.path.exists(saved_dir):
        os.makedirs(saved_dir)

    saved_file = os.path.join(saved_dir, "index.html")
    with open(saved_file, "w") as f:
        f.write(resp.text)


def main():
    for fetch_item in global_config.fetch_list:
        fetch_html(fetch_item)


if __name__ == "__main__":
    main()
