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

"""Abstract and concrete schema classes."""

import abc
import json
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Literal, Optional, Union
from uuid import UUID

import fastavro
import fastavro.types

SchemaVersionStatus = Literal['AVAILABLE', 'DELETING', 'FAILURE', 'PENDING']
SchemaFormat = Literal['AVRO', 'JSON']


class BaseSchema(abc.ABC):
    @property
    @abc.abstractmethod
    def data_format(self) -> SchemaFormat:
        """The data format of this schema."""

    @property
    @abc.abstractmethod
    def fully_qualified_name(self) -> str:
        """The fully-qualified name of this schema."""

    @abc.abstractmethod
    def read(self, bytes_: bytes, reader_schema: Optional["BaseSchema"] = None) -> Any:
        """Read bytes into a record."""

    @abc.abstractmethod
    def write(self, data) -> bytes:
        """Write a record into bytes."""

    @abc.abstractmethod
    def validate(self, data) -> None:
        """Raise a ValidationException if the data is invalid."""

    @abc.abstractmethod
    def json(self) -> str:
        """Return the JSON representation of this schema."""

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, BaseSchema)
            and self.data_format == other.data_format
            and self.fully_qualified_name == other.fully_qualified_name
        )


class AvroSchema(BaseSchema):
    """An Avro schema."""

    _definition: dict
    _parsed: fastavro.types.Schema

    def __init__(self, definition: Union[str, dict]) -> None:
        """Create a new AvroSchema."""
        definition = json.loads(definition) if isinstance(definition, str) else definition
        self._parsed = fastavro.parse_schema(definition)

    def __str__(self) -> str:
        return self.json()

    @property
    def data_format(self) -> SchemaFormat:
        return 'AVRO'

    @property
    def fully_qualified_name(self) -> str:
        # https://github.com/fastavro/fastavro/issues/415
        return self._parsed.get('name', self._parsed['type'])

    def read(self, bytes_: bytes, reader_schema: Optional[fastavro.types.Schema] = None) -> Any:
        b = BytesIO(bytes_)
        value = fastavro.schemaless_reader(
            b,
            self._parsed,
            reader_schema=reader_schema._parsed,
        )
        b.close()
        return value

    def write(self, data) -> bytes:
        b = BytesIO()
        fastavro.schemaless_writer(b, self._parsed, data)
        value = b.getvalue()
        b.close()
        return value

    def validate(self, data) -> None:
        fastavro.validate(data, self._parsed)

    def json(self) -> str:
        return json.dumps(self._parsed)

    def __getitem__(self, key: str):
        return self._definition[key]


@dataclass
class SchemaVersion:
    schema_name: str
    version_id: UUID
    definition: str
    data_format: SchemaFormat
    status: SchemaVersionStatus
    version_number: Optional[int] = None

    def __hash__(self):
        return hash(self.definition)
