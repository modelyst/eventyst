#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

import logging
from typing import Union

from eventyst.core import commands, events
from eventyst.service_layer import handler_registry, unit_of_work

logger = logging.getLogger(__name__)


class MessageBus:
    def __init__(
        self,
        uow: unit_of_work.AbstractUnitOfWork,
        handler_registry: handler_registry.HandlerRegistry,
    ):
        self.uow = uow
        self.handler_registry = handler_registry

    def handle(self, message: Union[commands.Command, events.Event]):
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message)
            elif isinstance(message, commands.Command):
                self.handle_command(message)
            else:
                raise Exception(f"{message} was not an Event or Command")

    def handle_event(self, event: events.Event):
        for handler in self.handler_registry.event_handlers.get(type(event), []):
            try:
                handler(event)
                self.queue.extend(self.uow.collect_new_events())
            except Exception:
                logger.exception(f"Exception handling event {event}")
                continue

    def handle_command(self, command: commands.Command):
        try:
            self.handler_registry.handle_command(command)
            self.queue.extend(self.uow.collect_new_events())
        except Exception:
            raise
