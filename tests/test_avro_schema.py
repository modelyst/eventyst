#   Copyright 2022 Modelyst LLC
#   All Rights Reserved


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
