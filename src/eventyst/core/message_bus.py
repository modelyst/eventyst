#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

import asyncio
from typing import TYPE_CHECKING, Optional, Union

from eventyst.core import commands, events
from eventyst.utilities.log import get_child_logger

if TYPE_CHECKING:
    from eventyst.adapters.kafka import EventBroker
    from eventyst.core.handler_registry import HandlerRegistry

logger = get_child_logger(__name__)


class MessageBus:
    def __init__(
        self,
        handler_registry: 'HandlerRegistry',
        event_broker: 'Optional[EventBroker]' = None,
    ):
        self.handler_registry = handler_registry

        # setup queue and loop
        self.queue: asyncio.Queue[Union[commands.Command, events.Event]] = asyncio.Queue()
        self.submissions = set()

        self.event_broker = event_broker

        # Events
        self._ready_event = asyncio.Event()
        self._stop_event = asyncio.Event()

    def _startup(self):
        self.loop = asyncio.get_running_loop()
        self._process_queue_task = self.loop.create_task(self.process_queue())
        # self.loop.create_task(self.queue_size_reporter(10))
        self._ready_event.set()

    async def handle(self, message: Union[commands.Command, events.Event]):
        if self._stop_event.is_set():
            raise Exception("MessageBus is stopped")
        await self.queue.put(message)

    async def process_queue(self):
        while not self._stop_event.is_set():
            try:
                message = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            if isinstance(message, events.Event):
                await self.handle_event(message)
            elif isinstance(message, commands.Command):
                await self.handle_command(message)
            else:
                raise Exception(f"{message} was not an Event or Command")
            self.queue.task_done()
        logger.debug("MessageBus stopped")

    async def handle_event(self, event: events.Event):
        task = self.loop.create_task(self.handler_registry.handle_event(event, self, self.event_broker))
        self.submissions.add(task)
        task.add_done_callback(lambda _: self.submissions.remove(task))

    async def handle_command(self, command: commands.Command):
        task = self.loop.create_task(self.handler_registry.handle_command(command, self))
        self.submissions.add(task)
        task.add_done_callback(lambda _: self.submissions.remove(task))

    async def __aenter__(self):
        self._startup()
        return self

    async def __aexit__(self, exc_type=None, exc_val=None, exc_tb=None):
        await self.shutdown()

    async def shutdown(self):
        await self.queue.join()
        await asyncio.gather(*self.submissions)
        self._stop_event.set()
        await self._process_queue_task

    async def wait_until_ready(self):
        await self._ready_event.wait()

    async def queue_size_reporter(self, interval: float = 1.0):
        while not self._stop_event.is_set():
            logger.info(f"Queue size: {self.queue.qsize()}")
            await asyncio.sleep(interval)

    async def _entrypoint(self):
        self.loop = asyncio.get_event_loop()
        async with self:
            await self.wait_until_ready()
            await self._stop_event.wait()

    async def enqueue(self, message: Union[commands.Command, events.Event]):
        await self.queue.put(message)

    def enqueue_sync(self, message: Union[commands.Command, events.Event]):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(self.handle(message))

    def start(self):
        asyncio.run(self._entrypoint())

    def override_dependency(self, dependency, value):
        self.handler_registry.override_dependency(dependency, value)
