#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

import logging

from rich.console import Console
from rich.logging import RichHandler

from eventyst.configuration import settings

_ROOT_LOGGER_NAME = "eventyst"

console = Console()


def setup_logger():
    logger = logging.getLogger(_ROOT_LOGGER_NAME)
    logger.setLevel(settings.LOG_LEVEL.get_log_level())
    handler = RichHandler(console=console)
    handler.setLevel(settings.LOG_LEVEL.get_log_level())
    logger.addHandler(handler)
    return logger


def get_logger():
    return logging.getLogger(_ROOT_LOGGER_NAME)


def get_child_logger(name: str):
    # check if name begins with root logger name
    if name.startswith(_ROOT_LOGGER_NAME):
        # get root
        root = get_logger()
        return root.getChild(name[len(_ROOT_LOGGER_NAME) + 1 :])

    return logging.getLogger(name)


root = setup_logger()
