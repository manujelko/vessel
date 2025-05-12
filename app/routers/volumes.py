# app/routers/volumes.py
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from podman import PodmanClient
from podman.errors import APIError, NotFound

from app.dependencies import get_podman_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/volumes", tags=["volumes"])


@router.get("")
def list_volumes(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
) -> list[dict[str, Any]]:
    try:
        volumes = podman_client.volumes.list()
        return [v.attrs for v in volumes]
    except APIError:
        logger.exception("Failed to list volumes")
        raise HTTPException(status_code=500, detail="Failed to list volumes")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_volume(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    name: str = Body(..., embed=True, description="Name of the volume"),
    driver: str = Body("local", embed=True, description="Driver to use"),
    labels: dict[str, str] | None = Body(
        None, embed=True, description="Optional labels"
    ),
    options: dict[str, str] | None = Body(
        None, embed=True, description="Driver options"
    ),
) -> dict[str, Any]:
    try:
        volume = podman_client.volumes.create(
            name=name,
            driver=driver,
            labels=labels or {},
            options=options or {},
        )
        return volume.attrs
    except APIError:
        logger.exception("Failed to create volume")
        raise HTTPException(status_code=500, detail="Failed to create volume")


@router.get("/{volume_name}")
def inspect_volume(
    volume_name: str,
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
) -> dict[str, Any]:
    try:
        volume = podman_client.volumes.get(volume_name)
        return volume.attrs
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Volume '{volume_name}' not found")
    except APIError:
        logger.exception("Failed to inspect volume")
        raise HTTPException(status_code=500, detail="Failed to inspect volume")


@router.delete("/{volume_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_volume(
    volume_name: str,
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    force: bool = Query(False, description="Force deletion even if in use"),
) -> None:
    try:
        volume = podman_client.volumes.get(volume_name)
        volume.remove(force=force)
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Volume '{volume_name}' not found")
    except APIError as e:
        if e.status_code == 409:
            raise HTTPException(status_code=409, detail=e.explanation)
        logger.exception("Failed to delete volume")
        raise HTTPException(status_code=500, detail="Failed to delete volume")
