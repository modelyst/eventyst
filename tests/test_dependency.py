#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

from contextlib import AsyncExitStack

import pytest

from eventyst.core.commands import Command
from eventyst.core.dependency import (
    DependencyTracker,
    build_dependency_tracker,
    dependency,
    solve_dependency_tracker,
)
from eventyst.core.events import Event
from eventyst.core.handler_registry import HandlerRegistry
from eventyst.core.message_bus import MessageBus


def test_injection_of_message_bus():
    @dependency
    def fake_dependency(test_bus: MessageBus):
        return test_bus

    tracker = build_dependency_tracker(fake_dependency)
    assert isinstance(tracker, DependencyTracker)
    assert tracker.parameter_name_message_bus == "test_bus"


def test_async_handler():
    @dependency
    def fake_dependency(test_bus: MessageBus):
        return test_bus

    async def handler(event: Event, message_bus: MessageBus):
        return event

    tracker = build_dependency_tracker(dependency(handler))
    assert isinstance(tracker, DependencyTracker)
    assert tracker.parameter_name_message_bus == "message_bus"
    assert tracker.payload_name == "event"


@pytest.mark.asyncio
async def test_solving_dependency_tracker():
    class TestEvent(Event):
        value: int

    @dependency
    def first_dependency(event: TestEvent):
        return event.value

    @dependency
    async def second_dependency(first_dep: int = first_dependency):
        return first_dep + 1

    def handler(
        event: TestEvent,
        message_bus: MessageBus,
        dep_2: int = second_dependency,
    ):
        return event.value + dep_2, message_bus

    main = dependency(handler)
    tracker = build_dependency_tracker(main)
    bus = MessageBus(HandlerRegistry())
    payload = TestEvent(value=1)
    async with AsyncExitStack() as stack:
        values, cache = await solve_dependency_tracker(tracker=tracker, payload=payload, message_bus=bus, stack=stack)
    assert values == {"dep_2": 2, "message_bus": bus, "event": payload}
    assert cache == {second_dependency.dependency: 2, first_dependency.dependency: 1}

    result = tracker.call(**values)
    assert result == (3, bus)


def test_multiple_events_throws_error():
    def handler(
        event_1: Event,
        event_2: Event,
    ):
        pass

    with pytest.raises(ValueError, match="Cannot have multiple events or commands as a dependency for"):
        build_dependency_tracker(dependency(handler))


def test_command_and_event_throws_error():
    def handler(
        event_1: Event,
        command_1: Command,
    ):
        pass

    with pytest.raises(ValueError, match="Cannot have multiple events or commands as a dependency for"):
        build_dependency_tracker(dependency(handler))


def test_handler_payload_type_auto_detected():
    class TestEvent1(Event):
        value_1: int

    def handler(event_1: TestEvent1):
        pass

    tracker = build_dependency_tracker(dependency(handler))
    assert tracker.payload_type == TestEvent1


def test_sub_dependencies_disagree_with_dependency_event_or_command():
    class TestEvent1(Event):
        value_1: int

    class TestEvent2(Event):
        value_2: int

    @dependency
    def dep_1(event_2: TestEvent2):
        return 1

    def handler(event_1: TestEvent1, dep_1=dep_1):
        pass

    with pytest.raises(ValueError):
        build_dependency_tracker(dependency(handler))


@pytest.mark.asyncio
async def test_dependency_teardown():
    poke = False

    @dependency
    def dep():
        nonlocal poke
        poke = True
        yield poke
        print('test')
        poke = False

    def handler(dep=dep):
        dep.append(1)

    tracker = build_dependency_tracker(dependency(handler))
    async with AsyncExitStack() as stack:
        await solve_dependency_tracker(tracker=tracker, payload=None, message_bus=None, stack=stack)
        assert poke

    assert not poke


@pytest.mark.asyncio
async def test_async_dependency_teardown():
    poke = False

    @dependency
    async def dep():
        nonlocal poke
        poke = True
        yield poke
        poke = False

    def handler(dep=dep):
        dep.append(1)

    tracker = build_dependency_tracker(dependency(handler))
    async with AsyncExitStack() as stack:
        await solve_dependency_tracker(tracker=tracker, payload=None, message_bus=None, stack=stack)
        assert poke

    assert not poke
