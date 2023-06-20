#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

"""Welcome to Eventyst!"""
import hashlib
from uuid import UUID

from eventyst.core.application import Eventyst  # noqa: F401
from eventyst.core.commands import Command  # noqa: F401
from eventyst.core.dependency import dependency  # noqa: F401
from eventyst.core.events import Event  # noqa: F401
from eventyst.core.message_bus import MessageBus  # noqa: F401

__author__ = "Michael Statt"
__email__ = "michael.statt@modelyst.io"
__maintainer__ = "Michael Statt"
__maintainer_email__ = "michael.statt@modelyst.io"
__version__ = "0.0.1"


version_uuid = UUID(hashlib.md5(__version__.encode()).hexdigest())
