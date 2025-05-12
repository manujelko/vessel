from fastapi import FastAPI

from app.routers import containers, images, info, login, logs

app = FastAPI(
    title="Podman API",
    description="REST API for Podman container management",
)

app.include_router(router=images.router, prefix="/api")
app.include_router(router=login.router, prefix="/api")
app.include_router(router=containers.router, prefix="/api")
app.include_router(router=info.router, prefix="/api")
app.include_router(router=logs.router, prefix="/api")
