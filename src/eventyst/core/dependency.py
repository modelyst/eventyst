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

import inspect
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from functools import partial
from itertools import chain
from typing import Any, Callable, Generic, Iterable, Optional, Type, TypeVar, Union

from eventyst.adapters.kafka import EventBroker
from eventyst.core.commands import Command
from eventyst.core.events import BaseMessage, Event
from eventyst.core.message_bus import MessageBus
from eventyst.utilities.function_inspection import lenient_issubclass

T = TypeVar("T")


class Dependency(Generic[T]):
    parameter_name_message_bus: Optional[str]

    def __init__(
        self,
        dependency: Callable[..., T],
        *,
        cache: bool = True,
        emitted_types: Iterable[Type[BaseMessage]] | None = None,
    ):
        self.dependency = dependency
        self.cache = cache
        self.emitted_types = set(emitted_types or [])

    def __call__(self, *args, **kwargs) -> Any:
        if self.dependency is None:
            raise TypeError("Dependency not set")
        return self.dependency(*args, **kwargs)


class DependencyTracker:
    def __init__(
        self,
        *,
        name: Optional[str] = None,
        call: Callable[..., Any],
        cache: bool = True,
        parameter_name_message_bus: Optional[str] = None,
        parameter_name_context: Optional[str] = None,
        parameter_name_event_broker: Optional[str] = None,
        payload_name: Optional[str] = None,
        payload_type: Optional[Type[Event] | Type[Command]] = None,
        dependencies: Optional[dict[str, 'DependencyTracker']] = None,
        emitted_types: Iterable[Type[BaseMessage]] | None = None,
    ) -> None:
        self.call = call
        self.cache = cache
        self.name = name
        self.parameter_name_message_bus = parameter_name_message_bus
        self.parameter_name_context = parameter_name_context
        self.parameter_name_event_broker = parameter_name_event_broker
        self.payload_name = payload_name
        self.payload_type = payload_type
        self.dependencies = dependencies or {}
        self.emitted_types = set(emitted_types or [])


def dependency(
    function: Callable[..., Any] = None, *, cache: bool = True, emitted_types: Iterable[Type[BaseMessage]] | None = None
) -> Any:
    emitted_types = chain(emitted_types or [], getattr(function, "__emitted_types__", []))
    if function is None:
        return partial(dependency, cache=cache, emitted_types=emitted_types)
    return Dependency(function, cache=cache, emitted_types=emitted_types)


def get_handler_tracker(
    function: Callable[..., T], emitted_types: Iterable[Type[BaseMessage]] | None = None
) -> DependencyTracker:
    return build_dependency_tracker(dependency(function), emitted_types=emitted_types)


def build_dependency_tracker(
    dependency: Dependency, name: Optional[str] = None, emitted_types: Iterable[Type[BaseMessage]] | None = None
) -> DependencyTracker:
    if not isinstance(dependency, Dependency):
        raise TypeError("Input must be an instance of Dependency")

    tracker = DependencyTracker(
        call=dependency.dependency,
        cache=dependency.cache,
        name=name,
        emitted_types=emitted_types,
    )

    signature = inspect.signature(dependency.dependency)
    for name, param in signature.parameters.items():
        annotation, sub_dependency = analyze_signature_parameter(name, param)
        if sub_dependency is not None:
            evaluated_dependency = build_dependency_tracker(
                sub_dependency, name=name, emitted_types=sub_dependency.emitted_types
            )
            tracker.emitted_types.update(evaluated_dependency.emitted_types)
            tracker.dependencies[name] = evaluated_dependency

        if annotation != inspect.Parameter.empty:
            set_default_param_names(name, annotation, tracker)

    # Check the return type and if its an event, set the emitted type
    if signature.return_annotation != inspect.Signature.empty:
        annotation = signature.return_annotation
        if lenient_issubclass(annotation, Event):
            tracker.emitted_types.add(annotation)
    # Iterate through dependencies and ensure that there is only a single payload type
    payload_types = set()
    for sub_tracker in tracker.dependencies.values():
        if sub_tracker.payload_type is not None:
            payload_types.add(sub_tracker.payload_type)

    if tracker.payload_type is not None:
        payload_types.add(tracker.payload_type)

    if len(payload_types) > 1:
        raise ValueError(f"Multiple Payload types defined for {tracker.call}\n")

    if tracker.payload_type is None and len(payload_types) > 0:
        tracker.payload_type = payload_types.pop()

    return tracker


async def solve_dependency_tracker(
    *,
    tracker: DependencyTracker,
    payload: Union[Command, Event],
    stack: AsyncExitStack,
    context: Optional[dict[str, Any]] = None,
    message_bus: Optional[MessageBus] = None,
    overrides: Optional[dict[Type, Any]] = None,
    cache: Optional[dict[Callable[..., Any], Any]] = None,
) -> tuple[dict[str, Any], dict[Callable[..., Any], Any]]:
    """Iterates through the dependency tracker and returns a the inputs for the underlying callable."""
    if not isinstance(tracker, DependencyTracker):
        raise TypeError("Input must be an instance of DependencyTracker")

    cache = cache or {}
    overrides = overrides or {}
    inputs: dict[str, Any] = {}
    # iterate through the dependency tracker and solve all sub-dependencies recursively
    for name, sub_tracker in tracker.dependencies.items():
        sub_inputs, sub_cache = await solve_dependency_tracker(
            tracker=sub_tracker,
            payload=payload,
            cache=cache,
            message_bus=message_bus,
            stack=stack,
            overrides=overrides,
        )

        # update the cache
        cache.update(sub_cache)
        # Inject the default values
        if sub_tracker.parameter_name_event_broker is not None:
            assert sub_tracker.parameter_name_event_broker is not None, "Event Broker not set"
            sub_inputs[sub_tracker.parameter_name_event_broker] = overrides[EventBroker]

        if sub_tracker.parameter_name_message_bus is not None:
            sub_inputs[sub_tracker.parameter_name_message_bus] = message_bus

        if sub_tracker.parameter_name_context is not None:
            sub_inputs[sub_tracker.parameter_name_context] = context

        if sub_tracker.payload_name is not None:
            sub_inputs[sub_tracker.payload_name] = payload

        call = sub_tracker.call
        call = overrides.get(call, call)
        # Check cache for dependency
        if tracker.call in cache:
            sub_output = cache[call]
        elif inspect.isasyncgenfunction(call):
            cm = asynccontextmanager(call)(**sub_inputs)
            sub_output = await stack.enter_async_context(cm)
        elif inspect.isgeneratorfunction(call):
            cm = contextmanager(call)(**sub_inputs)
            sub_output = stack.enter_context(cm)
        elif inspect.iscoroutinefunction(call):
            sub_output = await call(**sub_inputs)
        else:
            sub_output = call(**sub_inputs)

        # If the dependency has a name it is an input to the parent dependency
        if sub_tracker.name is not None:
            inputs[name] = sub_output

        # If the dependency is not cached yet, add it to the cache
        if sub_tracker.cache and sub_tracker.call not in cache:
            cache[sub_tracker.call] = sub_output

    if tracker.parameter_name_event_broker is not None:
        assert tracker.parameter_name_event_broker is not None, "Event Broker not set"
        inputs[tracker.parameter_name_event_broker] = overrides[EventBroker]

    # Inject the default values for the input dependency
    if tracker.parameter_name_message_bus is not None:
        inputs[tracker.parameter_name_message_bus] = message_bus

    if tracker.parameter_name_context is not None:
        inputs[tracker.parameter_name_context] = context

    if tracker.payload_name is not None:
        inputs[tracker.payload_name] = payload

    return inputs, cache


def set_default_param_names(param_name: str, annotation: Any, tracker: DependencyTracker) -> DependencyTracker:
    """Search through the signature of the dependency's callable and set the param names that map to default values."""

    if lenient_issubclass(annotation, MessageBus):
        if tracker.parameter_name_message_bus:
            raise ValueError(
                f"Cannot have multiple message buses as a dependency for {tracker.call}\n"
                f"parameters {tracker.parameter_name_message_bus} and {param_name} both define a subclass of MessageBus"
            )
        tracker.parameter_name_message_bus = param_name
    elif lenient_issubclass(annotation, (Event, Command)):
        if tracker.payload_name is not None:
            raise ValueError(
                f"Cannot have multiple events or commands as a dependency for {tracker.call}\n"
                f"parameters {tracker.payload_name} and {param_name} both define a subclass of Event or Command"
            )
        tracker.payload_name = param_name
        tracker.payload_type = annotation
    elif lenient_issubclass(annotation, EventBroker):
        if tracker.parameter_name_event_broker is not None:
            raise ValueError(
                f"Cannot have multiple events or commands as a dependency for {tracker.call}\n"
                f"parameters {tracker.payload_name} and {param_name} both define a subclass of Event or Command"
            )
        tracker.parameter_name_event_broker = param_name
    return tracker


_RESERVED_INJECTION_TYPES = (MessageBus, Event, Command, EventBroker)


def analyze_signature_parameter(parameter_name: str, parameter: inspect.Parameter) -> tuple[Any, Optional[Dependency]]:
    # Set default outputs
    annotation = Any
    dependency = None
    # Check if the default value is a dependency
    if isinstance(parameter.default, Dependency):
        dependency = parameter.default
    # Extract the annotation
    if parameter.annotation != inspect.Parameter.empty:
        annotation = parameter.annotation

    if dependency is not None and lenient_issubclass(annotation, _RESERVED_INJECTION_TYPES):
        raise ValueError(
            f"Cannot use {dependency} as a dependency for {parameter_name} because it is a reserved injection type"
        )
    return annotation, dependency
