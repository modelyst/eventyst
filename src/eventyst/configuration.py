#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

"""
Settings needed for each GCLD mircoservice to communicate with one another.

This includes the ports for the API and for Kafka as well as all of the
information needed to access the database.
"""

import os
from textwrap import dedent

from pydantic import BaseSettings, PostgresDsn, SecretStr, parse_obj_as


class PostgresqlDsn(PostgresDsn):
    """Restricts allowed schema for PostgresDsn Pydantic Model to postgresql."""

    allowed_schemes = {"postgresql"}


class Settings(BaseSettings):
    """
    GCLD Settings Management Object that carries the global configuration for the GCLD application.

    Inherits from the Pydantic BaseSettings object (https://pydantic-docs.helpmanual.io/usage/settings/) to set the
    configuration from environment variables, dotenv files and defaults.
    """

    # Top Level GCLDSettings
    APPLICATION_PATH: str = "gcld.core.application:default_app"
    MACHINE_NAME: str = "Unknown Machine"
    # Kafka Settings
    KAFKA_HOST: str = "kafka"
    KAFKA_PORT: int = 9092
    # API Settings
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"
    API_PREFIX: str = "/api"

    # Local Settings
    DATA_PATH: str = "/usr/src/gcld/src/data"

    # Database Credentials
    POSTGRES_DSN: PostgresqlDsn = parse_obj_as(PostgresqlDsn, "postgresql://postgres@localhost/gcld")
    POSTGRES_PASSWORD: SecretStr = SecretStr("")
    POSTGRES_SCHEMA: str = "public"

    class Config:
        """Pydantic Configuration."""

        env_file = os.environ.get("GCLD_ENV_FILE", ".env")
        env_prefix = "GCLD_"

    @property
    def broker_url(self):
        """Generate the URI for the Kafka cluster from the KAFKA_PORT and KAFKA_HOST settings."""
        return f"{self.KAFKA_HOST}:{self.KAFKA_PORT}"

    def display(self, show_defaults: bool = False, show_passwords: bool = False):
        """Display a valid dotenv file version of the settings for human readability and logging."""
        params = []
        for key, val in self.dict().items():
            if val is not None:
                str_val = f"{val.get_secret_value()}" if show_passwords and "PASSWORD" in key else val
                if show_defaults or key in self.__fields_set__:
                    params.append(f"GCLD_{key} = {str_val}")
                else:
                    params.append(f"# GCLD_{key} = {str_val}")

        params_str = "\n".join(params)
        output = f"""######################\n# GCLD Settings\n######################\n{params_str}"""
        return dedent(output)

    def __str__(self) -> str:
        """Use the human readable display method for printing."""
        return self.display()


# Instantiate the global settings for use throughout GCLD
settings = Settings()
