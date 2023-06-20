#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

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
