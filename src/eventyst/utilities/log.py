#   Copyright 2023 Modelyst LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

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
