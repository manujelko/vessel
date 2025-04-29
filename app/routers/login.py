from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from podman import PodmanClient
from podman.errors import APIError

from app.dependencies import get_podman_client

router = APIRouter(prefix="/login", tags=["login"])


@router.post("/repository")
def login_repository(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    username: str = Body(..., description="Registry username"),
    password: str = Body(..., description="Registry password"),
    registry: str = Body("docker.io", description="Registry URL (default: docker.io)"),
) -> dict:
    """
    Login to a container registry.

    This endpoint authenticates with a container registry using the provided credentials.
    After successful authentication, you can pull images from private repositories.

    Example (login to Docker Hub):
    ```JSON
    {
      "username": "myuser",
      "password": "mypassword"
    }
    ```

    Example with custom registry:
    ```JSON
    {
      "username": "myuser",
      "password": "mypassword",
      "registry": "registry.example.com"
    }
    ```
    """
    try:
        result = podman_client.login(
            username=username, password=password, registry=registry
        )

        return {
            "status": "success",
            "message": f"Successfully logged in to {registry}",
            "details": result,
        }
    except APIError:
        raise HTTPException(status_code=401, detail="Authentication failed")
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error")
