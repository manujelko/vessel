# app/routers/logs.py
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from podman import PodmanClient
from podman.errors import APIError, NotFound

from app.dependencies import get_podman_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/{container_id}")
def get_logs_json(
    container_id: str,
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    stdout: bool = Query(True),
    stderr: bool = Query(True),
    since: str | None = Query(None),
    tail: int | str | None = Query(None),
) -> list[str]:
    try:
        container = podman_client.containers.get(container_id)
        logs = container.logs(
            stream=False, stdout=stdout, stderr=stderr, since=since, tail=tail
        )

        lines = []
        if isinstance(logs, bytes):
            lines = logs.decode("utf-8").splitlines()
        elif isinstance(logs, str):
            lines = logs.splitlines()
        elif hasattr(logs, "__iter__"):
            for part in logs:
                if isinstance(part, bytes):
                    lines.extend(part.decode("utf-8").splitlines())
                else:
                    lines.extend(str(part).splitlines())
        else:
            lines = [str(logs)]

        return lines
    except NotFound:
        raise HTTPException(
            status_code=404, detail=f"Container {container_id} not found"
        )
    except APIError:
        logger.exception("Error fetching logs for container %s", container_id)
        raise HTTPException(status_code=500, detail="Error fetching logs")
    except Exception:
        logger.exception("Unexpected error while retrieving logs")
        raise HTTPException(status_code=500, detail="Unexpected error")


@router.get("/{container_id}/stream")
def stream_logs(
    container_id: str,
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    stdout: bool = Query(True),
    stderr: bool = Query(True),
    since: str | None = Query(None),
    tail: int | str | None = Query(None),
) -> StreamingResponse:
    try:
        container = podman_client.containers.get(container_id)
        logs = container.logs(
            stream=True,
            stdout=stdout,
            stderr=stderr,
            since=since,
            tail=tail,
        )

        def iter_logs():
            try:
                for chunk in logs:
                    yield chunk if isinstance(chunk, bytes) else str(chunk).encode()
            except Exception:
                logger.exception("Error while streaming logs")
                yield b"\n[ERROR] Stream interrupted.\n"

        return StreamingResponse(iter_logs(), media_type="text/plain")

    except NotFound:
        raise HTTPException(
            status_code=404, detail=f"Container {container_id} not found"
        )
    except APIError:
        logger.exception("Error streaming logs for container %s", container_id)
        raise HTTPException(status_code=500, detail="Error streaming logs")
    except Exception:
        logger.exception("Unexpected error while streaming logs")
        raise HTTPException(status_code=500, detail="Unexpected error")
