from typing import Annotated
from fastapi import APIRouter, Depends
from app.dependencies import get_podman_client
from podman import PodmanClient

router = APIRouter(prefix="/images", tags=["images"])


@router.get("")
def get_images(podman_client: Annotated[PodmanClient, Depends(get_podman_client)]):
    return podman_client.images.list()
