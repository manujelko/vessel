from typing import Annotated, List, Dict, Union, Literal
from fastapi import APIRouter, Depends, HTTPException, Body
from app.dependencies import get_podman_client
from podman import PodmanClient
from podman.errors import APIError, ImageNotFound
from app.models import ImageModel

router = APIRouter(prefix="/images", tags=["images"])


@router.get("")
def get_images(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
) -> list[ImageModel]:
    """
    Get a list of all images.

    Returns a list of image objects with details including ID, repository, tag, and registry.
    """
    images = podman_client.images.list()
    result = []

    for image in images:
        # If the image has tags, create an ImageModel for each tag
        if hasattr(image, "tags") and image.tags:
            for tag in image.tags:
                # Parse the tag string to extract registry, repository, and tag
                parts = tag.split("/")
                if ":" in parts[-1]:
                    repo_and_tag = parts[-1].split(":")
                    repository = repo_and_tag[0]
                    tag_value = repo_and_tag[1]
                else:
                    repository = parts[-1]
                    tag_value = None

                # Determine the registry (everything before the repository)
                registry = None
                if len(parts) > 1:
                    registry = "/".join(parts[:-1])

                result.append(
                    ImageModel(
                        id=image.id,
                        repository=repository,
                        tag=tag_value,
                        registry=registry,
                        full_name=tag,
                    )
                )
        # If the image has no tags, create an ImageModel with just the ID
        else:
            result.append(
                ImageModel(
                    id=image.id,
                    repository="<none>",
                    tag=None,
                    registry=None,
                    full_name=image.id,
                )
            )

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
    ```JSON
    {
      "repository": "nginx",
      "tag": "1.21.0"
    }
    ```

    Example with custom registry without authentication:
    ```JSON
    {
      "repository": "myapp",
      "tag": "1.0",
      "registry": "registry.example.com"
    }
    ```

    Example with custom registry and authentication:
    ```JSON
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


@router.get("/{image_id}")
def get_image(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    image_id: str,
) -> ImageModel:
    """
    Get an image by its ID.

    This endpoint retrieves details of a specific image identified by its ID.

    Returns an image object with details including ID, repository, tag, and registry.
    """
    try:
        # Get the image by ID
        image = podman_client.images.get(image_id)

        # If the image has tags, use the first tag to create the ImageModel
        if hasattr(image, "tags") and image.tags:
            tag = image.tags[0]

            # Parse the tag string to extract registry, repository, and tag
            parts = tag.split("/")
            if ":" in parts[-1]:
                repo_and_tag = parts[-1].split(":")
                repository = repo_and_tag[0]
                tag_value = repo_and_tag[1]
            else:
                repository = parts[-1]
                tag_value = None

            # Determine the registry (everything before the repository)
            registry = None
            if len(parts) > 1:
                registry = "/".join(parts[:-1])

            return ImageModel(
                id=image.id,
                repository=repository,
                tag=tag_value,
                registry=registry,
                full_name=tag,
            )
        # If the image has no tags, create an ImageModel with just the ID
        else:
            return ImageModel(
                id=image.id,
                repository="<none>",
                tag=None,
                registry=None,
                full_name=image.id,
            )
    except ImageNotFound:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.delete("/{image_id}")
def delete_image(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    image_id: str,
    force: bool = False,
) -> Dict[
    str,
    Union[
        str,
        List[
            Dict[Literal["Deleted", "Untagged", "Errors", "ExitCode"], Union[str, int]]
        ],
    ],
]:
    """
    Delete an image from the local storage by its ID.

    This endpoint removes an image from the local storage. The image must be specified by its ID.
    If the image is in use by a container, the deletion will fail unless the 'force' parameter is set to true.

    Returns a dictionary with status information and details about deleted/untagged images.
    """
    try:
        # Remove the image
        result = podman_client.images.remove(image=image_id, force=force)

        return {
            "status": "success",
            "message": f"Image {image_id} deleted successfully",
            "details": result,
        }
    except ImageNotFound:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Error deleting image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
