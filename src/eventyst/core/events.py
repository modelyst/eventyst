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

import datetime
import io
import json
from typing import Any
from uuid import UUID, uuid4, uuid5

import avro.errors
import avro.schema
from avro.io import BinaryDecoder, BinaryEncoder, DatumReader, DatumWriter
from pydantic import BaseModel, create_model

from eventyst.configuration import settings
from eventyst.schema import AvroSchema
from eventyst.utilities.avro_schema import schema


class EventMetadata(BaseModel):
    id: UUID
    created_at: float
    event_type: str
    source: str
    source_ids: list[UUID] | None = None


class BaseMessage(BaseModel):
    __namespace__ = "eventyst.core.message"

    @classmethod
    def avro_schema(cls) -> AvroSchema:
        envelope = create_model(
            cls.__name__ + "Envelope",
            metadata=(EventMetadata, ...),
            payload=(cls, ...),
        )
        # TODO solve issue with list arrays
        return AvroSchema(schema(envelope, namespace=cls.__namespace__))

    @classmethod
    def topic(cls) -> str:
        suffix = getattr(cls, "__topic__", cls.__name__)
        return settings.SERVICE_NAME + f"-{suffix}"

    def envelope(self, source_ids: list[UUID] | None = None) -> dict[str, Any]:
        now = datetime.datetime.now()
        return {
            "metadata": EventMetadata(
                id=uuid5(uuid4(), settings.SERVICE_NAME),
                created_at=now.timestamp(),
                event_type=self.__class__.__name__,
                source=settings.SERVICE_NAME,
                source_ids=source_ids,
            ).dict(),
            "payload": self.dict(),
        }

    def serialize(self) -> bytes:
        # Serialize the object to Avro format
        schema = avro.schema.parse(json.dumps(self.avro_schema()))
        writer = DatumWriter(schema)
        bytes_writer = io.BytesIO()
        encoder = BinaryEncoder(bytes_writer)
        writer.write(self.envelope(), encoder)
        return bytes_writer.getvalue()

    @classmethod
    def deserialize(cls, serialized_data):
        # Deserialize Avro data to create a new object of the subclass
        schema = avro.schema.parse(json.dumps(cls.avro_schema()))
        reader = DatumReader(schema)
        bytes_reader = io.BytesIO(serialized_data)
        decoder = BinaryDecoder(bytes_reader)
        try:
            data = reader.read(decoder)
        except avro.errors.InvalidAvroBinaryEncoding as e:
            raise ValueError(f"Invalid Avro encoding: {e}")

        if not isinstance(data, dict):
            raise ValueError(f"Invalid Avro encoding: {data}")

        obj = cls.parse_obj(data["payload"])
        metadata = EventMetadata.parse_obj(data["metadata"])
        return obj, metadata


class Event(BaseMessage):
    """Base class for all events."""

    __namespace__ = "eventyst.core.events"
