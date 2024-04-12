import os
import requests
import htmlmin
import time

import config
from logger import init_logger

global_config = config.load_config()
logger = init_logger()


def replace_html(html: str, current_fetch_item: config.FetchItem) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')

    element = soup.find('a', {'href': global_config.url_prefix + "public"})
    if element is not None:
        element.extract()

    element = soup.find('div', {'id': 'menuDefault'}).find('ul')
    if element is not None:
        element.extract()

    element = soup.find('a', {'href': global_config.url_prefix + "login"})
    if element is not None:
        element.extract()

    element = soup.find('div', {'class': 'dropdown'})
    if element is not None:
        element.insert_after(soup.new_tag('br'))
        element.extract()

    html = str(soup)

    flag_div = '<div class="collapse navbar-collapse" id="menuDefault">'

    board_menu = '''
<ul class="navbar-nav mr-auto">
    '''

    for item in global_config.fetch_list:
        board_menu += '''
    <li class="nav-item {active}">
        <a class="nav-link" href="{show_url}">{show_name}</a>
    </li>
        '''.format(
            active="active" if item.dir_name == current_fetch_item.dir_name else "",
            show_url=item.show_url,
            show_name=item.show_name,
        )

    board_menu += "</ul>"

    html = html.replace(flag_div, flag_div + board_menu)

    html = html.replace("'" + global_config.url_prefix +
                        "public'", "'" + current_fetch_item.show_url + "'")

    return html


def replace_assets_url(html: str) -> str:
    if global_config.assets_url is None:
        return html

    html = html.replace(global_config.url_prefix, global_config.assets_url)
    return html


def minify_html(html: str) -> str:
    html = htmlmin.minify(html)
    return html


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

    html = resp.text
    html = replace_html(html, fetch_item)
    html = replace_assets_url(html)
    html = minify_html(html)

    saved_file = os.path.join(saved_dir, "index.html")
    with open(saved_file, "w") as f:
        f.write(html)


def main():
    while True:
        try:
            for fetch_item in global_config.fetch_list:
                fetch_html(fetch_item)
        except Exception as e:
            logger.error(e)

        time.sleep(global_config.refresh_time)


if __name__ == "__main__":
    main()
