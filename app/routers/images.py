from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Body
from app.dependencies import get_podman_client
from podman import PodmanClient
from podman.errors import APIError, ImageNotFound

router = APIRouter(prefix="/images", tags=["images"])


@router.get("")
def get_images(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
) -> list[str]:
    """
    Get a list of all images.

    Returns a list of strings that fully identify each image with its registry, name, and version.
    """
    images = podman_client.images.list()
    result = []

    for image in images:
        # If the image has tags, use them to identify the image
        if hasattr(image, "tags") and image.tags:
            for tag in image.tags:
                result.append(tag)
        # If the image has no tags, use its ID
        else:
            result.append(image.id)

    return result


@router.post("/pull")
def pull_image(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    repository: str = Body(..., description="Repository to pull from"),
    tag: str = Body("latest", description="Image tag to pull"),
    registry: str | None = Body(None, description="Registry URL (default: docker.io)"),
    username: str | None = Body(None, description="Registry username (optional)"),
    password: str | None = Body(None, description="Registry password (optional)"),
) -> dict[str, str]:
    """
    Pull an image from a registry.

    By default, this endpoint pulls from the official Docker registry without authentication.
    You can optionally provide a custom registry with credentials.

    Example (pull nginx from Docker Hub):
    ```json
    {
      "repository": "nginx",
      "tag": "1.21.0"
    }
    ```

    Example with custom registry without authentication:
    ```json
    {
      "repository": "myapp",
      "tag": "1.0",
      "registry": "registry.example.com"
    }
    ```

    Example with custom registry and authentication:
    ```json
    {
      "repository": "myapp",
      "tag": "1.0",
      "registry": "registry.example.com",
      "username": "myuser",
      "password": "mypassword"
    }
    ```
    """
    try:
        # Prepare the full repository name with registry if provided
        full_repository = repository
        if registry:
            full_repository = f"{registry}/{repository}"

        # Login to the registry if credentials are provided
        auth_config = None
        if username and password:
            podman_client.login(username=username, password=password, registry=registry)
            auth_config = {"username": username, "password": password}

        # Pull the image
        _ = podman_client.images.pull(
            repository=full_repository,
            tag=tag,
            auth_config=auth_config,
        )

        return {
            "status": "success",
            "message": f"Image {repository}:{tag} pulled successfully",
        }
    except ImageNotFound:
        raise HTTPException(
            status_code=404, detail=f"Image {repository}:{tag} not found"
        )
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Error pulling image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
