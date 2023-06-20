#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

"""
Settings needed for each Eventyst mircoservice to communicate with one another.

This includes the ports for the API and for Kafka as well as all of the
information needed to access the database.
"""

import os
from textwrap import dedent

from pydantic import BaseSettings, PostgresDsn, SecretStr, parse_obj_as

from eventyst._enums import LogLevel

# PREFIX for all environment variables
_PACKAGE_PREFIX = "EVENTYST_"


class PostgresqlDsn(PostgresDsn):
    """Restricts allowed schema for PostgresDsn Pydantic Model to postgresql."""

    allowed_schemes = {"postgresql+psycopg"}


class Settings(BaseSettings):
    """
    Eventyst Settings Management Object that carries the global configuration for the Eventyst application.

    Inherits from the Pydantic BaseSettings object (https://pydantic-docs.helpmanual.io/usage/settings/) to set the
    configuration from environment variables, dotenv files and defaults.
    """

    SERVICE_NAME: str = "eventyst"
    APPLICATION_PATH: str = 'model::app'
    # Kafka Settings
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    # Local Settings
    LOG_LEVEL: LogLevel = LogLevel.INFO
    # Database Credentials
    POSTGRES_DSN: PostgresqlDsn = parse_obj_as(PostgresqlDsn, "postgresql+psycopg://postgres@localhost/eventyst")
    POSTGRES_PASSWORD: SecretStr = SecretStr("")
    POSTGRES_SCHEMA: str = "public"
    ENGINE_ECHO: bool = False
    APP_STR: str = "model.main:app"
    # AWS Settings
    AWS_SCHEMA_REGISTRY_NAME: str = "eventyst"
    AWS_SCHEMA_REGISTRY_REGION: str = "us-east-2"

    class Config:
        """Pydantic Configuration."""

        env_file = os.environ.get("EVENTYST_ENV_FILE", ".env")
        env_prefix = _PACKAGE_PREFIX

    def display(self, show_defaults: bool = False, show_passwords: bool = False):
        """Display a valid dotenv file version of the settings for human readability and logging."""
        params = []
        for key, val in self.dict().items():
            if val is not None:
                str_val = f"{val.get_secret_value()}" if show_passwords and "PASSWORD" in key else val
                if show_defaults or key in self.__fields_set__:
                    params.append(f"{_PACKAGE_PREFIX}{key} = {str_val}")
                else:
                    params.append(f"# {_PACKAGE_PREFIX}{key} = {str_val}")

        params_str = "\n".join(params)
        output = f"""######################\n# EVENTYST Settings\n######################\n{params_str}"""
        return dedent(output)

    def __str__(self) -> str:
        """Use the human readable display method for printing."""
        return self.display()


# Instantiate the global settings for use throughout Eventyst
settings = Settings()
