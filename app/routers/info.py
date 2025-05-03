from typing import Annotated, Any

from fastapi import APIRouter, Depends
from podman import PodmanClient

from app.dependencies import get_podman_client

router = APIRouter(prefix="/info", tags=["info"])


@router.get("")
def get_info(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
) -> dict[str, Any]:
    info = podman_client.info()
    return info
