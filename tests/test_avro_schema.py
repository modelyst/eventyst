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

from eventyst.core.events import Event
from eventyst.schema import AvroSchema


def test_schema():
    class TestEvent(Event):
        """Test event."""

        a: int
        b: str

    assert isinstance(TestEvent.avro_schema(), AvroSchema)


def test_schema_namespace():
    class TestEvent(Event):
        """Test event."""

        __namespace__ = "test.namespace"
        a: int
        b: str

    assert TestEvent.avro_schema()["namespace"] == "test.namespace"


def test_schema_default():
    """Tests that a default value is correctly handled."""

    class TestEvent(Event):
        """Test event."""

        b: str = "default"

    expected_schema = {
        "type": "record",
        "name": "TestEvent",
        "namespace": "eventyst.core.events",
        "doc": "Test event.",
        "fields": [
            {"name": "b", "type": "string", "default": "default"},
        ],
    }

    schema = TestEvent.avro_schema()
    payload_schema = [field for field in schema["fields"] if field["name"] == "payload"]
    assert len(payload_schema) == 1
    assert payload_schema[0]['type'] == expected_schema
