from fastapi import FastAPI
from app.routers import images

app = FastAPI(
    title="Podman API",
    description="REST API for Podman container management",
)

app.include_router(router=images.router, prefix="/api")
