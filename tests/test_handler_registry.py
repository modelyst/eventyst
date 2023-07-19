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

import pytest

from eventyst.core.events import Event
from eventyst.core.handler_registry import HandlerRegistry
from eventyst.core.message_bus import MessageBus


def test_basic_registration():
    handler_registry = HandlerRegistry()

    class TestEvent(Event):
        pass

    @handler_registry.register
    def handler(event: TestEvent):
        pass


def test_register_fails_with_no_event():
    handler_registry = HandlerRegistry()

    with pytest.raises(ValueError, match=r"does not have a Command or Event as a parameter"):
        handler_registry.register(lambda: None)

    def handler():
        pass

    with pytest.raises(ValueError, match=r"does not have a Command or Event as a parameter"):
        handler_registry.register(handler)

    with pytest.raises(ValueError, match=r"does not have a Command or Event as a parameter"):

        @handler_registry.register
        def handler_with_args(bus: MessageBus):
            pass


def test_handler_still_callable_after_registration():
    handler_registry = HandlerRegistry()

    class TestEvent(Event):
        value: int

    @handler_registry.register
    def handler(event: TestEvent):
        return event.value

    assert handler(TestEvent(value=1)) == 1
