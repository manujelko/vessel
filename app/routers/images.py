from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Body
from app.dependencies import get_podman_client
from podman import PodmanClient
from podman.errors import APIError, ImageNotFound

router = APIRouter(prefix="/images", tags=["images"])


@router.get("")
def get(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
) -> list[str]:
    """
    Get a list of all images.

    Returns a list of image names (strings) that fully identify each image.
    """
    images = podman_client.images.list()
    result = []

    for image in images:
        # If the image has tags, add each tag to the result
        if hasattr(image, "tags") and image.tags:
            for tag in image.tags:
                result.append(tag)
        # If the image has no tags, use the image ID
        else:
            result.append(image.id)

    return result


@router.post("/pull")
def pull(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    image_name: str = Body(..., description="Image name to pull", embed=True),
) -> dict[str, str]:
    """
    Pull an image from a registry.

    This endpoint pulls an image using only the image name.
    For authentication, use the /login endpoint first.

    Example (pull nginx from Docker Hub):
    ```JSON
    {
      "image_name": "nginx:1.21.0"
    }
    ```

    Example with custom registry:
    ```JSON
    {
      "image_name": "registry.example.com/myapp:1.0"
    }
    ```
    """
    try:
        # Pull the image
        _ = podman_client.images.pull(image_name)

        return {
            "status": "success",
            "message": f"Image {image_name} pulled successfully",
        }
    except ImageNotFound:
        raise HTTPException(status_code=404, detail=f"Image {image_name} not found")
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Error pulling image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.delete("/{image_name:path}", status_code=204)
def delete(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    image_name: str,
    force: bool = False,
) -> None:
    """
    Delete an image from the local storage by its name.

    This endpoint removes an image from the local storage. The image must be specified by its name.
    If the image is in use by a container, the deletion will fail unless the 'force' parameter is set to true.

    Returns a 204 No Content status code on success.
    """
    try:
        # Remove the image
        podman_client.images.remove(image=image_name, force=force)
        # Return None (which FastAPI converts to a 204 No Content response)
        return None
    except ImageNotFound:
        raise HTTPException(status_code=404, detail=f"Image {image_name} not found")
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Error deleting image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
