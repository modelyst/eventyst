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

import asyncio
import threading
from typing import Any, Callable, Iterable, ParamSpec, Type, TypeVar

import boto3
from fastapi import Depends, FastAPI

from eventyst.adapters.aws.schema_registry import GlueSchemaRegistryClient
from eventyst.adapters.kafka import KafkaEventBroker
from eventyst.configuration import settings
from eventyst.core.commands import Command
from eventyst.core.events import BaseMessage, Event
from eventyst.core.handler_registry import HandlerRegistry
from eventyst.core.message_bus import MessageBus
from eventyst.serialization.serializers import DataAndSchema, Deserializer, Serializer
from eventyst.utilities.log import get_child_logger

logger = get_child_logger(__name__)

In = ParamSpec("In")
Out = TypeVar("Out")


class Eventyst:
    def __init__(self, name: str = "Eventyst", version: str = "0.1.0", registry: HandlerRegistry | None = None) -> None:
        self.name = name
        self.version = version
        self.registry = registry or HandlerRegistry()
        self.broker = None
        self.logger = get_child_logger(f"eventyst.{self.name}")

    def build_api(self):
        # iterate through registry and register routes
        app = FastAPI(title=self.name, version=self.version)

        @app.get("/")
        async def root():
            return {"message": "Hello World"}

        @app.get("/health")
        async def health():
            return {"message": "OK"}

        bus = MessageBus(self.registry)

        def message_bus():
            return bus

        async def submit_event(
            event: Event,
            bus: MessageBus = Depends(message_bus),
        ):
            await bus.handle(event)
            return event

        # override submit_event's event parameter to be an AnalysisRan
        for handler in self.registry.command_handlers.values():
            if handler.payload_type is None:
                continue
            submit_event.__annotations__["event"] = handler.payload_type
            app.post(
                f"/command/{handler.call.__name__.replace('_','-')}",
                summary=f"Submit a {handler.payload_type.__name__} Command",
                tags=["Command"],
            )(submit_event)
        return app, bus

    def register_with_broker(self, event: Type[Event]):
        # check if event is already registered
        if event in self.registry.broker_events:
            raise Exception(f"{event} is already registered with the broker")
        # check if event is an Event
        if not issubclass(event, Event):
            raise Exception(f"You can only register Events with the broker. {event} is not an Event")
        self.registry.broker_events.add(event)
        return event

    def start_api(self):
        app, bus = self.build_api()
        thread = threading.Thread(target=bus.start, daemon=True)
        thread.start()
        return app

    def produce(self, *events: BaseMessage, topic: str | None = None, raw_event: dict | None = None):
        logger.debug(f"Producing {len(events)} to {topic}")
        asyncio.run(self._single_producer(events, topic))

    def _initalize_broker(self):
        if self.broker is not None:
            return
        session = boto3.Session(region_name=settings.AWS_SCHEMA_REGISTRY_REGION)
        glue_client = session.client('glue')
        registry_client = GlueSchemaRegistryClient(
            glue_client=glue_client,
            registry_name=settings.AWS_SCHEMA_REGISTRY_NAME,
        )
        serializer = Serializer(
            client=registry_client,
        )
        deserializer = Deserializer(client=registry_client, reader_schema=BaseMessage.avro_schema())
        self.broker = KafkaEventBroker(
            settings.KAFKA_BOOTSTRAP_SERVERS,
            serializer=serializer,
            deserializer=deserializer,
            config_file=settings.KAFKA_CONNECTION_CONFIG_FILE,
        )

    async def _single_producer(self, events: BaseMessage, topic: str | None = None):
        self._initalize_broker()
        assert self.broker is not None, "Broker should be initialized"
        async with self.broker:
            for event in events:
                await self.broker.produce(event, topic)

    async def start_consumer(
        self,
        payload_type: Type[Command] | Type[Event],
        auto_offset_reset: str = "latest",
        group_id: str = "eventyst",
    ):
        session = boto3.Session()
        glue_client = session.client('glue')
        registry_client = GlueSchemaRegistryClient(
            glue_client=glue_client,
            registry_name=settings.AWS_SCHEMA_REGISTRY_NAME,
        )

        logger.info(f"Starting consumer for {payload_type.topic()}")
        serializer = Serializer(
            client=registry_client,
        )
        deserializer = Deserializer(client=registry_client, reader_schema=payload_type.avro_schema())
        broker = KafkaEventBroker(
            settings.KAFKA_BOOTSTRAP_SERVERS,
            serializer=serializer,
            deserializer=deserializer,
            config_file=settings.KAFKA_CONNECTION_CONFIG_FILE,
        )
        bus = MessageBus(self.registry, event_broker=broker)
        asyncio.create_task(bus._entrypoint())
        async with broker:
            await broker.producer.start()
            consumer = await broker.get_consumer(payload_type, auto_offset_reset, group_id)
            try:
                async for message in consumer:
                    try:
                        value: DataAndSchema = message.value
                        event = payload_type.parse_obj(value.data["payload"])
                        await bus.handle(event)
                    except Exception as e:
                        logger.error(f"An error occurred when handling message: {e}")
            finally:
                await consumer.stop()

    async def start_multiple_consumers(
        self,
        *payload_type_map: Type[Command] | Type[Event],
        group_id: str = "eventyst",
        auto_offset_reset: str = "latest",
    ):
        tasks = []
        for payload_type in payload_type_map:
            tasks.append(asyncio.create_task(self.start_consumer(payload_type, auto_offset_reset, group_id)))
        await asyncio.gather(*tasks)

    def register(
        self,
        handler: Callable[..., Any] | None = None,
        *,
        entrypoint: bool = False,
        emitted_types: Iterable[Type[BaseMessage]] | None = None,
    ):
        if handler:
            self.registry.register(handler, entrypoint=entrypoint, emitted_types=emitted_types)
            return handler
        else:

            def wrapper(handler_: Callable[..., Any]):
                self.registry.register(handler_, entrypoint=entrypoint, emitted_types=emitted_types)
                return handler_

            return wrapper

    def start(self, offset_reset: str = "latest", group_id: str = "eventyst"):
        if len(self.registry.entrypoints) == 0:
            raise Exception("No entrypoints registered")
        logger.info("Starting Eventyst")
        logger.info(f"Consuming from {len(self.registry.entrypoints)} topics")
        asyncio.run(
            self.start_multiple_consumers(*self.registry.entrypoints, group_id=group_id, auto_offset_reset=offset_reset)
        )
