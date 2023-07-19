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

"""Strategies for choosing schema names in the registry."""

from typing import Protocol

from eventyst.schema import BaseSchema


class SchemaNamingStrategy(Protocol):
    """Controls how schema names are chosen for a value.

    Arguments:
        topic: the name of the topic the value is being written into.
        value: the _unserialized_ value being written.
        is_key: whether the value is a Kafka key or value.

    Returns:
        str: the schema name to use
    """

    def __call__(self, topic: str, is_key: bool, schema: BaseSchema) -> str:
        ...


def topic_name_strategy(topic: str, is_key: bool, schema: BaseSchema) -> str:
    """The default naming strategy.

    Message keys are `<topic>-key` and message values are
    `<topic>-value`.

    This is a sensible strategy for topics whose records follow a uniform
    schema, but does not allow mixing different schemas on the same topic.
    """
    return f"{topic}-{'key' if is_key else 'value'}"


def record_name_strategy(topic: str, is_key: bool, schema: BaseSchema) -> str:
    """Uses the fully-qualified record name as the schema name.

    Allows a topic to contain records with multiple incompatible schemas.
    However, this requires that the fully-qualified record names uniquely
    and consistently identify a schema across the entire registry.
    """
    return schema.fully_qualified_name


def topic_record_name_strategy(topic: str, is_key: bool, schema: BaseSchema) -> str:
    """Combines the topic and record name to form the schema name.

    Allows a topic to contain records with multiple incompatible schemas.
    Additionally allows different topics to use the same record name for
    incompatible schemas.
    """
    return f'{topic}-{schema.fully_qualified_name}'
