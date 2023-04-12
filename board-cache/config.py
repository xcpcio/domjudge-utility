import yaml
import os


class FetchItem:
    def __init__(self, url_suffix, dir_name):
        self.url_suffix = url_suffix
        self.dir_name = dir_name


class Config:
    def __init__(self, url, saved_dir, fetch_list):
        self.url = url
        self.saved_dir = saved_dir
        self.fetch_list = [FetchItem(**item) for item in fetch_list]


def load_config() -> Config:
    config_path = os.getenv("CONFIG_FILE_PATH", "./config.yaml")
    with open(config_path, "r") as f:
        yaml_data = f.read()

    data = yaml.load(yaml_data, Loader=yaml.Loader)
    config = Config(**data)
    return config
