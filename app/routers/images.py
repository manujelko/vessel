import datetime as dt
import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from podman import PodmanClient
from podman.errors import APIError, ImageNotFound

from app.dependencies import get_podman_client
from app.models import Image

logger = logging.getLogger(__name__)

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

    Example with a custom registry:
    ```JSON
    {
      "image_name": "registry.example.com/myapp:1.0"
    }
    ```
    """
    try:
        podman_client.images.pull(image_name)
        logger.info("Image %s pulled successfully", image_name)
        return None
    except ImageNotFound:
        logger.exception("Image not found")
        raise HTTPException(status_code=404, detail=f"Image {image_name} not found")
    except APIError:
        logger.exception("Error pulling image")
        raise HTTPException(status_code=500, detail="Error pulling image")
    except Exception:
        logger.exception("Unexpected error")
        raise HTTPException(status_code=500, detail="Unexpected error")


@router.delete("", status_code=204)
def delete_image(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    image_id: str | None = None,
    image_name: str | None = None,
    force: bool = False,
) -> None:
    """
    Delete an image from the local storage by its name or id.

    This endpoint removes an image from the local storage. The image must be specified by its name or id.
    If the image is in use by a container, the deletion will fail unless the 'force' parameter is set to true.

    Returns a 204 No Content status code on success.
    """

    match (image_id, image_name):
        case (None, None):
            logger.warning("Either image_id or image_name must be provided")
            raise HTTPException(
                status_code=400, detail="Either image_id or image_name must be provided"
            )
        case (None, str()):
            logger.info("Deleting image by name: %s", image_name)
            identifier = image_name
        case (str(), None):
            logger.info("Deleting image by id: %s", image_id)
            identifier = image_id
        case (str(), str()):
            logger.warning("Either image_id or image_name must be provided, not both")
            raise HTTPException(
                status_code=400,
                detail="Either image_id or image_name must be provided, not both",
            )
        case _:
            logger.error("Unexpected error; id=%s, name=%s", image_id, image_name)
            raise HTTPException(status_code=500, detail="Unexpected error")

    try:
        podman_client.images.remove(image=identifier, force=force)
        logger.info("Image %s deleted successfully", identifier)
        return None
    except ImageNotFound:
        logger.exception("Image not found")
        raise HTTPException(status_code=404, detail=f"Image {image_name} not found")
    except APIError as e:
        if e.status_code == 409:
            logger.exception("Image is in use by a container")
            raise HTTPException(status_code=409, detail=e.explanation)
        else:
            logger.exception("Error deleting image")
            raise HTTPException(status_code=500, detail="Error deleting image")
    except Exception:
        logger.exception("Unexpected error")
        raise HTTPException(status_code=500, detail="Unexpected error")
