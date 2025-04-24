from typing import Any, Generator

from podman import PodmanClient
from podman.errors import APIError
from fastapi import HTTPException

from app.settings import settings


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
            raise HTTPException(
                status_code=503,
                detail=f"Cannot connect to podman socket at {settings.podman_socket}",
            )
        else:
            yield client
