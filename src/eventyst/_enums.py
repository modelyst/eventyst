#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

import logging
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def get_log_level(self):
        return getattr(logging, self)
