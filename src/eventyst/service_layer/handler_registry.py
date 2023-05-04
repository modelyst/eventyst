#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

import inspect
from typing import Any, Callable, Dict, List, Type

from eventyst.core import commands, events


class HandlerRegistry:
    command_handlers: Dict[Type[commands.Command], Callable[..., Any]]
    event_handlers: Dict[Type[events.Event], List[Callable[..., Any]]]

    def __init__(
        self,
        event_handlers: Dict[Type[events.Event], List[Callable]] | None = None,
        command_handlers: Dict[Type[commands.Command], Callable] | None = None,
    ):
        self.event_handlers = event_handlers or {}
        self.command_handlers = command_handlers or {}

    def register_event(self, event_class: Type[events.Event]) -> Callable[[Callable], Callable]:
        def decorator(handler: Callable) -> Callable:
            self.register_events({event_class: [handler]})
            return handler

        return decorator

    def register_command(self, command_class: Type[commands.Command]) -> Callable[[Callable], Callable]:
        def decorator(handler: Callable) -> Callable:
            self.register_commands({command_class: handler})
            return handler

        return decorator

    def register_commands(self, handlers: Dict[Type[commands.Command], Callable[..., Any]]):
        # check for duplicate command handlers
        duplicate_handlers = set(handlers.keys()) & set(self.command_handlers.keys())
        if duplicate_handlers:
            raise ValueError(f"Duplicate command handlers for commands {duplicate_handlers}")
        self.command_handlers.update(handlers)

    def register_events(self, handlers: Dict[Type[events.Event], List[Callable[..., Any]]]):
        for event_type, event_handlers in handlers.items():
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].extend(event_handlers)

    def handle_command(self, command: commands.Command, *args, **kwargs) -> Any:
        handler = self.command_handlers.get(type(command))
        if handler is None:
            raise ValueError(f"No handler registered for command {type(command)}")
        return handler(command, *args, **kwargs)

    def inject_dependencies(self, dependencies: Dict[str, Any]):
        injected_command_handlers = {
            command: self.inject_dependencies_into_handler(handler, dependencies)
            for command, handler in self.command_handlers.items()
        }
        injected_event_handlers = {}
        for event, handlers in self.event_handlers.items():
            injected_event_handlers[event] = [
                self.inject_dependencies_into_handler(handler, dependencies) for handler in handlers
            ]
        return HandlerRegistry(
            injected_event_handlers,
            injected_command_handlers,
        )

    @staticmethod
    def inject_dependencies_into_handler(handler, dependencies):
        params = inspect.signature(handler).parameters
        deps = {name: dependency for name, dependency in dependencies.items() if name in params}
        return lambda message: handler(message, **deps)


handler_registry = HandlerRegistry()
