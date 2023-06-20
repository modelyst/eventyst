#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

import asyncio
import inspect
import logging
from contextlib import AsyncExitStack
from functools import partial
from typing import TYPE_CHECKING, Callable, Dict, Iterable, List, ParamSpec, Type, TypeVar

from eventyst.core import commands, events
from eventyst.core.dependency import DependencyTracker, get_handler_tracker, solve_dependency_tracker

if TYPE_CHECKING:
    from eventyst.adapters.kafka import EventBroker
    from eventyst.service_layer.message_bus import MessageBus

P = ParamSpec('P')
R = TypeVar('R')

logger = logging.getLogger(__name__)


class HandlerRegistry:
    command_handlers: Dict[Type[commands.Command], DependencyTracker]
    event_handlers: Dict[Type[events.Event], List[DependencyTracker]]

    def __init__(
        self,
        event_handlers: Dict[Type[events.Event], List[DependencyTracker]] | None = None,
        command_handlers: Dict[Type[commands.Command], DependencyTracker] | None = None,
        broker_events: set[Type[events.Event]] | None = None,
    ):
        self.event_handlers = event_handlers or {}
        self.command_handlers = command_handlers or {}
        self.broker_events = broker_events or set()
        self.entrypoints = set()
        self.overrides = {}

    def register(
        self,
        handler: Callable[P, R],
        entrypoint: bool = True,
        emitted_types: Iterable[Type[events.BaseMessage]] | None = None,
    ) -> Callable[P, R]:
        tracker = get_handler_tracker(handler, emitted_types)
        if tracker.payload_type is None:
            raise ValueError(f"Handler {handler} does not have a Command or Event as a parameter")
        elif issubclass(tracker.payload_type, events.Event):
            self.register_events({tracker.payload_type: [tracker]})
        elif issubclass(tracker.payload_type, commands.Command):
            self.register_commands({tracker.payload_type: tracker})
        else:
            raise ValueError(f"Handler {handler} has unsupported payload type {tracker.payload_type}")

        if entrypoint:
            self.entrypoints.add(tracker.payload_type)
        return handler

    def register_commands(self, handlers: Dict[Type[commands.Command], DependencyTracker]):
        # check for duplicate command handlers
        duplicate_handlers = set(handlers.keys()) & set(self.command_handlers.keys())
        if duplicate_handlers:
            raise ValueError(f"Duplicate command handlers for commands {duplicate_handlers}")
        self.command_handlers.update(handlers)

    def register_events(self, handlers: Dict[Type[events.Event], List[DependencyTracker]]):
        for event_type, event_handlers in handlers.items():
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].extend(event_handlers)

    def get_event_handlers(self, event: events.Event) -> List[DependencyTracker]:
        return self.event_handlers.get(type(event), [])

    def get_command_handler(self, command: commands.Command) -> DependencyTracker:
        if type(command) not in self.command_handlers:
            raise ValueError(f"No handler registered for commands of type {type(command)}")
        return self.command_handlers[type(command)]

    async def handle_event(
        self,
        event: events.Event,
        bus: 'MessageBus',
        broker: 'EventBroker | None' = None,
    ):
        loop = asyncio.get_running_loop()
        tasks = []
        for handler in self.get_event_handlers(event):
            tasks.append(loop.create_task(self.call_handler(handler, event, bus)))

        if event.__class__ in self.broker_events and broker is not None:
            logger.debug(f"Producing event {event} to broker")
            tasks.append(loop.create_task(broker.produce(event)))
        return await asyncio.gather(*tasks)

    async def call_handler(
        self,
        handler: DependencyTracker,
        event: events.Event,
        bus: 'MessageBus',
    ):
        loop = asyncio.get_running_loop()
        async with AsyncExitStack() as stack:
            try:
                inputs, _ = await solve_dependency_tracker(
                    tracker=handler,
                    payload=event,
                    message_bus=bus,
                    stack=stack,
                    overrides=self.overrides,
                )
                if inspect.iscoroutinefunction(handler.call):
                    output = await handler.call(**inputs)
                else:
                    output = await loop.run_in_executor(None, partial(handler.call, **inputs))
                if output is not None and isinstance(output, events.Event):
                    await bus.enqueue(output)
            except Exception:
                logger.exception(f"Exception handling event {event}")

    async def handle_command(
        self,
        command: commands.Command,
        bus: 'MessageBus',
    ):
        loop = asyncio.get_running_loop()
        handler = self.get_command_handler(command)
        async with AsyncExitStack() as stack:
            inputs, _ = await solve_dependency_tracker(
                tracker=handler,
                payload=command,
                message_bus=bus,
                stack=stack,
                overrides=self.overrides,
            )
            if inspect.iscoroutinefunction(handler.call):
                output = await handler.call(**inputs)
            else:
                output = await loop.run_in_executor(None, partial(handler.call, **inputs))
            if output is not None and isinstance(output, events.Event):
                await bus.enqueue(output)

    def override_dependency(
        self,
        dependency: Type,
        override,
    ):
        self.overrides[dependency] = override
