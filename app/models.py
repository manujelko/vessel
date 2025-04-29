import datetime as dt

from pydantic import BaseModel


class Image(BaseModel):
    id: str
    parent_id: str | None = None
    repo_tags: list[str]
    repo_digests: list[str] | None = None
    created: dt.datetime
    size: int
    shared_size: int | None = None
    virtual_size: int | None = None
    labels: dict[str, str] | None = None
    containers: int | None = None
    architecture: str | None = None
    os: str | None = None
    digest: str | None = None
    history: list[str] | None = None
    is_manifest_list: bool | None = None
    names: list[str] | None = None
