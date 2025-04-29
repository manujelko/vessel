import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from podman import PodmanClient
from podman.errors import APIError, ImageNotFound

from app.dependencies import get_podman_client
from app.models import Image

router = APIRouter(prefix="/images", tags=["images"])


@router.get("")
def get_images(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
) -> list[Image]:
    """Get a list of all images."""
    results = []
    for image in podman_client.images.list():
        attrs = image.attrs
        image_model = Image(
            id=attrs["Id"],
            parent_id=attrs.get("ParentId"),
            repo_tags=attrs.get("RepoTags", []),
            created=dt.datetime.fromtimestamp(attrs["Created"]),
            size=attrs["Size"],
            shared_size=attrs.get("SharedSize"),
            virtual_size=attrs.get("VirtualSize"),
            labels=attrs.get("Labels"),
            containers=attrs.get("Containers"),
            architecture=attrs.get("Arch"),
            os=attrs.get("Os"),
            digest=attrs.get("Digest"),
            history=attrs.get("History"),
            is_manifest_list=attrs.get("IsManifestList"),
            names=attrs.get("Names"),
        )
        results.append(image_model)
    return results


@router.post("/pull", status_code=status.HTTP_204_NO_CONTENT)
def pull_image(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    image_name: str = Body(..., description="Image name to pull", embed=True),
) -> None:
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
        return None
    except ImageNotFound:
        raise HTTPException(status_code=404, detail=f"Image {image_name} not found")
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Error pulling image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.delete("/{image_name:path}", status_code=204)
def delete_image(
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
        podman_client.images.remove(image=image_name, force=force)
        return None
    except ImageNotFound:
        raise HTTPException(status_code=404, detail=f"Image {image_name} not found")
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Error deleting image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
