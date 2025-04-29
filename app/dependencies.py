import logging
from typing import Any, Generator

from fastapi import HTTPException
from podman import PodmanClient
from podman.errors import APIError

from app.settings import settings

logger = logging.getLogger(__name__)


def get_podman_client() -> Generator[PodmanClient, Any, None]:
    """
    FastAPI dependency that provides a Podman client instance.

    Returns:
        PodmanClient: Instance of a Podman client for container management
    """
    with PodmanClient(base_url=settings.podman_socket) as client:
        try:
            client.ping()
        except APIError:
            logger.exception("Cannot connect to podman socket")
            raise HTTPException(
                status_code=503,
                detail=f"Cannot connect to podman socket at {settings.podman_socket}",
            )
        else:
            yield client
