from typing import Any, Generator

from podman import PodmanClient
from fastapi import HTTPException

from app.settings import settings


def get_podman_client() -> Generator[PodmanClient, Any, None]:
    """
    FastAPI dependency that provides a Podman client instance.

    Returns:
        PodmanClient: Instance of a Podman client for container management
    """
    client = PodmanClient(base_url=settings.podman_socket)

    try:
        client.ping()
        yield client
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to podman socket at {settings.podman_socket}: {str(e)}",
        )
    finally:
        client.close()
