from enum import Enum
from typing import Literal, Type

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    EnvSettingsSource,
    TomlConfigSettingsSource,
)


class AppEnv(str, Enum):
    PROD = "prod"
    STAGE = "staging"
    DEV = "dev"
    LOCAL = "local"


class Logging(BaseModel):
    level: Literal["trace", "debug", "info", "warn", "error", "notset"]


class Redis(BaseModel):
    nodes: list[str]


class MySQL(BaseModel):
    host: str
    port: int
    username: str
    password: str
    database: str


class Settings(BaseSettings):
    logging: Logging
    redis: Redis
    mysql: MySQL
    model_config = SettingsConfigDict(toml_file="resource/config/project-local.toml")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings], **kwargs,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            EnvSettingsSource(settings_cls),
            TomlConfigSettingsSource(settings_cls),
        )


class LocalSettings(Settings):
    model_config = SettingsConfigDict(toml_file="resource/config/project-local.toml")


class DevSettings(Settings):
    model_config = SettingsConfigDict(toml_file="project-dev.toml")


class StageSettings(Settings):
    model_config = SettingsConfigDict(toml_file="project-stage.toml")


class ProdSettings(Settings):
    model_config = SettingsConfigDict(toml_file="resource/config/project-prod.toml")


settings = LocalSettings()
print(settings)

settings = ProdSettings()
print(settings)

