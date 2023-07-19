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

import abc
import json
from pathlib import Path
from typing import AsyncIterable, Type

from aiokafka import AIOKafkaClient, AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError, KafkaError

from eventyst._exceptions import BrokerConnectionError
from eventyst.core.events import BaseMessage, Event
from eventyst.serialization.registry import SchemaRegistryClient
from eventyst.serialization.serializers import Deserializer, Serializer
from eventyst.utilities.log import get_child_logger

logger = get_child_logger(__name__)


class EventBroker(abc.ABC):
    @abc.abstractmethod
    async def produce(self, event: Event, topic: str | None = None):
        pass

    @abc.abstractmethod
    async def get_consumer(self, payload_type: Type[BaseMessage], topic: str):
        pass


class Consumer(abc.ABC, AsyncIterable):
    @abc.abstractmethod
    async def start(self):
        pass

    @abc.abstractmethod
    async def stop(self):
        pass


def load_kafka_config_file(config_file: Path | None) -> dict:
    # Load config file if provided
    if config_file is None:
        return {}
    try:
        json_config = json.loads(config_file.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse config file: {e}")
    return json_config


class KafkaEventBroker(EventBroker):
    def __init__(
        self,
        bootstrap_servers: str,
        registry_client: SchemaRegistryClient | None = None,
        serializer: Serializer | None = None,
        deserializer: Deserializer = None,
        config_file: Path | None = None,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.registry_client = registry_client
        self.deserializer = deserializer
        self.serializer = serializer
        self.config = load_kafka_config_file(config_file)
        self._consumers = []

    async def test_connection(self):
        client = AIOKafkaClient(bootstrap_servers=self.bootstrap_servers)
        try:
            await client.bootstrap()
        except KafkaConnectionError:
            raise BrokerConnectionError("Could not connect to Kafka broker, please check your settings")

    async def start_producer(self):
        # check if producer is already started
        if self.producer._sender is None:
            try:
                await self.producer.start()
            except Exception as e:
                logger.debug(f"An error occurred when starting the producer: {e}")

    async def get_consumer(
        self,
        payload_type: Type[BaseMessage],
        auto_offset_reset: str = 'earliest',
        group_id: str = 'latest',
        topic: str | None = None,
    ) -> Consumer:
        topic = topic or payload_type.topic()
        # check if consumer is already started
        consumer = AIOKafkaConsumer(
            topic,
            **self.config,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset=auto_offset_reset,
            group_id=group_id,
            value_deserializer=self.deserializer,
        )
        consumer.subscribe([topic])
        await consumer.start()
        return consumer

    async def produce(self, event: Event, topic: str | None = None):
        # Override topic if provided
        topic = topic or event.topic()
        await self.start_producer()
        if self.serializer is not None:
            self.producer._value_serializer = self.serializer.get_serializer(topic)
        try:
            try:
                logger.debug(f"Producing event: {event}")
                await self.producer.send(topic, (event.envelope(), event.avro_schema()))
            except KafkaError as e:
                logger.debug(f"An error occurred when sending event: {e}")
        except Exception as e:
            logger.error(f"An error occurred when sending event: {e}", exc_info=e)

    async def __aenter__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            **self.config,
        )
        await self.producer.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.debug("Flushing and stopping producer")
        await self.producer.stop()
        logger.debug("Stopping consumers")
        for consumer in self._consumers:
            await consumer.stop()
