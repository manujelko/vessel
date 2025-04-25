from fastapi import FastAPI
from app.routers import images
from app.routers import login

app = FastAPI(
    title="Podman API",
    description="REST API for Podman container management",
)

app.include_router(router=images.router, prefix="/api")
app.include_router(router=login.router, prefix="/api")
