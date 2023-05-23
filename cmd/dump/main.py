#! /usr/bin/env python3

import yaml

from domjudge_utility import Dump, DumpConfig


def load_config():
    config_path = './config.yaml'
    with open(config_path, 'r') as f:
        config = DumpConfig(yaml.load(f, Loader=yaml.FullLoader))
        return config


def main():
    config = load_config()

    d = Dump(config)
    d.init_logging()
    d.dump()


if __name__ == '__main__':
    main()
