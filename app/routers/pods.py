# app/routers/pods.py
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from podman import PodmanClient
from podman.errors import APIError, NotFound

from app.dependencies import get_podman_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pods", tags=["pods"])


@router.get("")
def list_pods(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    all: bool = Query(False, description="Show all pods (including exited)"),
) -> list[dict[str, Any]]:
    try:
        pods = podman_client.pods.list(all=all)
        return [pod.attrs for pod in pods]
    except APIError:
        logger.exception("Failed to list pods")
        raise HTTPException(status_code=500, detail="Failed to list pods")


@router.get("/{pod_id}")
def inspect_pod(
    pod_id: str,
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
) -> dict[str, Any]:
    try:
        pod = podman_client.pods.get(pod_id)
        return pod.attrs
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Pod '{pod_id}' not found")
    except APIError:
        logger.exception("Failed to inspect pod")
        raise HTTPException(status_code=500, detail="Failed to inspect pod")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_pod(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    name: str = Body(..., embed=True, description="Name of the pod"),
    labels: dict[str, str] | None = Body(None, embed=True),
    ports: list[str] | None = Body(None, embed=True, description="Port mappings"),
    share: str | None = Body(None, embed=True, description="Namespace sharing mode"),
) -> dict[str, Any]:
    try:
        pod = podman_client.pods.create(
            name=name,
            labels=labels or {},
            ports=ports or [],
            share=share,
        )
        return pod.attrs
    except APIError:
        logger.exception("Failed to create pod")
        raise HTTPException(status_code=500, detail="Failed to create pod")


@router.delete("/{pod_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pod(
    pod_id: str,
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    force: bool = Query(False, description="Force delete running pod"),
) -> None:
    try:
        pod = podman_client.pods.get(pod_id)
        pod.remove(force=force)
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Pod '{pod_id}' not found")
    except APIError as e:
        if e.status_code == 409:
            raise HTTPException(status_code=409, detail=e.explanation)
        logger.exception("Failed to delete pod")
        raise HTTPException(status_code=500, detail="Failed to delete pod")
