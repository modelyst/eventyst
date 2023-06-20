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

from dataclasses import dataclass
from typing import Literal, Mapping, Optional, Protocol
from uuid import UUID

SchemaVersionStatus = Literal['AVAILABLE', 'DELETING', 'FAILURE', 'PENDING']
SchemaFormat = Literal['AVRO', 'JSON']
SchemaCompatibilityMode = Literal['BACKWARD', 'FORWARD', 'FULL', 'NONE']


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


class SchemaRegistryClient(Protocol):
    """Protocol for schema registries."""

    def get_schema_version(self, version_id: UUID) -> SchemaVersion:
        ...

    def register_schema_version(self, schema_name: str, definition: str) -> SchemaVersion:
        ...

    def create_schema(self, schema_name: str, definition: str) -> SchemaVersion:
        ...

    def get_schema_by_definition(self, schema_name: str, definition: str) -> SchemaVersion:
        ...

    def get_or_register_schema_version(
        self,
        schema_name: str,
        definition: str,
        data_format: SchemaFormat,
        compatibility_mode: SchemaCompatibilityMode,
    ) -> SchemaVersion:
        ...

    def put_schema_version_metadata(version_id: UUID, metadata: Mapping[str, str]) -> None:
        ...
