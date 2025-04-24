import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="vessel_")

    podman_socket: str = "unix:///run/podman/podman.sock"


settings = Settings()
