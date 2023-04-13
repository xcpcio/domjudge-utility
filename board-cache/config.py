import yaml
import os


class FetchItem:
    def __init__(self, url_suffix, dir_name, show_name, show_url):
        self.url_suffix = url_suffix
        self.dir_name = dir_name
        self.show_name = show_name
        self.show_url = show_url


class Config:
    def __init__(self, url, url_prefix, saved_dir, assets_url, fetch_list):
        self.url = url
        self.url_prefix = url_prefix
        self.saved_dir = saved_dir
        self.assets_url = assets_url
        self.fetch_list = [FetchItem(**item) for item in fetch_list]


def load_config() -> Config:
    config_path = os.getenv("CONFIG_FILE_PATH", "./config.yaml")
    with open(config_path, "r") as f:
        yaml_data = f.read()

    data = yaml.load(yaml_data, Loader=yaml.Loader)
    config = Config(**data)
    return config
