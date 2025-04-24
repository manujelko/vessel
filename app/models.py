from pydantic import BaseModel, Field


class ImageModel(BaseModel):
    """Model representing an image with its details."""

    id: str = Field(..., description="The image ID")
    repository: str = Field(..., description="The image repository")
    tag: str | None = Field(None, description="The image tag")
    registry: str | None = Field(
        None, description="The registry where the image is stored"
    )
    full_name: str = Field(
        ...,
        description="The full name of the image including registry, repository, and tag",
    )
