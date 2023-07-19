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

import functools
from typing import Any, Callable, NamedTuple
from uuid import UUID

from eventyst.schema import AvroSchema, BaseSchema
from eventyst.serialization.codec import decode, encode
from eventyst.serialization.naming import SchemaNamingStrategy, topic_name_strategy
from eventyst.serialization.registry import SchemaCompatibilityMode, SchemaRegistryClient, SchemaVersion
from eventyst.utilities.log import get_child_logger

logger = get_child_logger(__name__)


class DataAndSchema(NamedTuple):
    """Data and its schema.

    Can be used to wrap the data and schema together before calling the
    producer's producing methods.
    """

    data: Any
    schema: BaseSchema


class Serializer:
    """Kafka serializer that uses the AWS Schema Registry.

    Arguments:
        client: instance of SchemaRegistryClient
        is_key (optional): whether the serializer is serializing keys as
            opposed to values. Defaults to false. Setting this to the
            appropriate value is important to avoid mixing key and value
            schemas if using the default schema name strategy.
        compatibility_mode (optional): the compatibility mode t use if
            creating a new schema in the registry. Defaults to the
            registry's default compatibility setting if not specified.
        schema_naming_strategy (optional): how to choose the schema name
            when creating new schemas. Defaults to the topic name
            strategy. See the `naming` module for more information and
            alternate strategies.
    """

    def __init__(
        self,
        client: SchemaRegistryClient,
        is_key: bool = False,
        compatibility_mode: SchemaCompatibilityMode = 'BACKWARD',
        schema_naming_strategy: SchemaNamingStrategy = topic_name_strategy,
    ):
        self.client = client
        self.is_key = is_key
        self.compatibility_mode: SchemaCompatibilityMode = compatibility_mode
        self.schema_naming_strategy = schema_naming_strategy

    def get_serializer(self, topic: str) -> Callable[[DataAndSchema], bytes]:
        """Returns a serializer function for the given topic.

        The serializer function takes a single argument, the data to
        serialize, and returns the serialized bytes.

        Arguments:
            topic: the topic to serialize data for
        """
        return functools.partial(self.serialize, topic)

    def serialize(self, topic: str, data_and_schema: DataAndSchema) -> bytes:
        if data_and_schema is None:
            return None
        if not isinstance(data_and_schema, tuple):
            raise TypeError('KafkaSerializer can only serialize', f' {tuple}, got {type(data_and_schema)}')
        data, schema = data_and_schema
        schema_version = self._get_schema_version(topic, schema)
        serialized = schema.write(data)
        return encode(serialized, schema_version.version_id)

    @functools.lru_cache(maxsize=None)
    def _get_schema_version(self, topic: str, schema: BaseSchema) -> SchemaVersion:
        schema_name = self.schema_naming_strategy(topic, self.is_key, schema)
        logger.debug('Fetching schema %s...', schema_name)
        return self.client.get_or_register_schema_version(
            definition=schema.json(),
            schema_name=schema_name,
            data_format=schema.data_format,
            compatibility_mode=self.compatibility_mode,
        )


class Deserializer:
    """Kafka serializer that uses a Schema Registry.

    Arguments:
        client: instance of SchemaRegistryClient.
        secondary_deserializer: optional deserializer to pass through
            to when processing values with an unrecognized encoding.
            This is primarily use to migrate from other schema
            registries or handle schema-less data. The secondary deserializer
            should either be a callable taking the same arguments as
            deserialize or an object with a matching deserialize method.
    """

    def __init__(
        self,
        client: SchemaRegistryClient,
        reader_schema: BaseSchema = None,
        reader_schema_id: UUID = None,
    ):
        self.client = client
        self.reader_schema = reader_schema
        self.schema_version_id = reader_schema_id

    def __call__(self, bytes_: bytes) -> DataAndSchema:
        return self.deserialize(bytes_)

    def deserialize(self, bytes_: bytes) -> DataAndSchema:
        if bytes_ is None:
            return None
        data_bytes, schema_version_id = decode(bytes_)
        writer_schema_version = self._get_schema_version(schema_version_id)
        writer_schema = self._schema_for_version(writer_schema_version)

        # If the reader schema is not set, use the writer schema.
        if self.reader_schema:
            reader_schema = self.reader_schema
        elif self.schema_version_id:
            reader_schema_version = self._get_schema_version(schema_version_id)
            reader_schema = self._schema_for_version(reader_schema_version)
        else:
            reader_schema = None

        # If the reader schema is set, validate the writer schema against it.
        message = writer_schema.read(data_bytes, reader_schema=reader_schema)

        return DataAndSchema(message, reader_schema)

    @functools.lru_cache(maxsize=None)
    def _get_schema_version(self, version_id: UUID):
        return self.client.get_schema_version(version_id)

    @functools.lru_cache(maxsize=None)
    def _schema_for_version(self, version: SchemaVersion) -> BaseSchema:
        if version.data_format == 'AVRO':
            return AvroSchema(version.definition)
        raise NotImplementedError("Only AVRO is supported at the moment.")
