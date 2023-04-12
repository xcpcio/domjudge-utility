import logging


def init_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)

    logger.addHandler(consoleHandler)

    return logger
