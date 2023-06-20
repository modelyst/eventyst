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


class EventystException(Exception):
    """Base class for all Eventyst exceptions."""


class SchemaRegistryException(EventystException):
    """Base class for all Schema Registry exceptions."""


class SchemaRegistryTimeoutError(SchemaRegistryException):
    """Raised when a timeout occurs while waiting for a response from the Schema Registry."""


class SchemaRegistryClientException(SchemaRegistryException):
    """Raised when there is an error with the Schema Registry client."""


class SchemaValidationError(EventystException):
    """Raised when there is an error validating a schema."""


class BrokerConnectionError(EventystException):
    """Raised when there is an error connecting to the broker."""
