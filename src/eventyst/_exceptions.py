#   Copyright 2022 Modelyst LLC
#   All Rights Reserved


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
