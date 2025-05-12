import logging
from enum import Enum
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from podman import PodmanClient
from podman.errors import APIError, ContainerError, ImageNotFound, NotFound

from app.dependencies import get_podman_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/containers", tags=["containers"])


class Status(str, Enum):
    created = "created"
    initialized = "initialized"
    running = "running"
    paused = "paused"
    exited = "exited"
    unknown = "unknown"


@router.get("")
def list_containers(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    all_: Annotated[
        bool, Query(alias="all", description="If False, only show running containers")
    ] = False,
    since: Annotated[
        str | None,
        Query(description="Show containers created after container name or id given."),
    ] = None,
    before: Annotated[
        str | None,
        Query(description="Show containers created before container name or id given."),
    ] = None,
    limit: Annotated[int, Query(description="Show last N created containers.")] = 0,
    status: Annotated[
        Status | None, Query(description="Show only containers with this status")
    ] = None,
    exited: Annotated[
        int | None, Query(description="Show only containers with this exit code")
    ] = None,
    id_: Annotated[
        str | None, Query(alias="id", description="Show only container with this id")
    ] = None,
    name: Annotated[
        str | None, Query(description="Show only container with this name")
    ] = None,
) -> list[dict[str, Any]]:
    """List containers."""
    filters: dict[str, Any] = {}

    if status is not None:
        filters["status"] = status.value
    if exited is not None:
        filters["exited"] = exited
    if id_ is not None:
        filters["id"] = id_
    if name is not None:
        filters["name"] = name

    try:
        containers = podman_client.containers.list(
            all=all_,
            since=since,
            before=before,
            limit=limit,
            filters=filters,
        )
    except APIError:
        logger.exception("Error listing containers")
        raise HTTPException(status_code=500, detail="Error listing containers")

    results = []
    for container in containers:
        attrs = container.attrs
        results.append(attrs)
    return results


@router.post("")
def run_container(
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    image_name: str = Body(..., description="Image name to run"),
    container_name: str | None = Body(None, description="Name for the container"),
    command: str | list[str] | None = Body(
        None, description="Command to run in the container"
    ),
    environment: dict[str, str] | None = Body(
        None, description="Environment variables"
    ),
    volumes: dict[str, dict[str, str]] | None = Body(
        None, description="Volumes to mount"
    ),
    detach: bool = Body(
        False, description="Run container in background and return container object"
    ),
    remove: bool = Body(False, description="Remove container when it exits"),
    auto_remove: bool = Body(
        False, description="Automatically remove the container when it exits"
    ),
    privileged: bool = Body(
        False, description="Give extended privileges to this container"
    ),
    network: str | None = Body(None, description="Connect the container to a network"),
    ports: dict[str, int | str | list[str]] | None = Body(
        None, description="Port mappings"
    ),
    user: str | None = Body(None, description="Username or UID to run the container"),
    working_dir: str | None = Body(
        None, description="Working directory inside the container"
    ),
    entrypoint: str | list[str] | None = Body(
        None, description="Overwrite the default ENTRYPOINT of the image"
    ),
    cap_add: list[str] | None = Body(None, description="Add Linux capabilities"),
    cap_drop: list[str] | None = Body(None, description="Drop Linux capabilities"),
    device_cgroup_rules: list[str] | None = Body(
        None, description="Add rules to the device cgroup"
    ),
    devices: list[str] | None = Body(
        None, description="Expose host devices to the container"
    ),
    dns: list[str] | None = Body(None, description="Set custom DNS servers"),
    dns_search: list[str] | None = Body(
        None, description="Set custom DNS search domains"
    ),
    extra_hosts: dict[str, str] | None = Body(
        None, description="Add hostname mappings"
    ),
    group_add: list[str] | None = Body(
        None, description="Add additional groups to join"
    ),
    init: bool | None = Body(None, description="Run an init inside the container"),
    ipc_mode: str | None = Body(None, description="IPC mode to use"),
    isolation: str | None = Body(None, description="Container isolation technology"),
    labels: dict[str, str] | None = Body(None, description="Container labels"),
    log_driver: str | None = Body(None, description="Logging driver for the container"),
    log_options: dict[str, str] | None = Body(None, description="Log driver options"),
    mac_address: str | None = Body(None, description="Container MAC address"),
    mem_limit: str | None = Body(None, description="Memory limit"),
    mem_reservation: str | None = Body(None, description="Memory soft limit"),
    memswap_limit: str | None = Body(
        None, description="Swap limit equal to memory plus swap"
    ),
    oom_kill_disable: bool | None = Body(None, description="Disable OOM Killer"),
    oom_score_adj: int | None = Body(None, description="Tune host's OOM preferences"),
    pid_mode: str | None = Body(None, description="PID mode to use"),
    pids_limit: int | None = Body(None, description="Tune container pids limit"),
    platform: str | None = Body(
        None, description="Platform in the format os[/arch[/variant]]"
    ),
    restart_policy: dict[str, Any] | None = Body(
        None, description="Restart policy to apply when a container exits"
    ),
    security_opt: list[str] | None = Body(None, description="Security options"),
    shm_size: str | None = Body(None, description="Size of /dev/shm"),
    stdin_open: bool | None = Body(
        None, description="Keep STDIN open even if not attached"
    ),
    stop_signal: str | None = Body(None, description="Signal to stop a container"),
    stop_timeout: int | None = Body(
        None, description="Timeout (in seconds) to stop a container"
    ),
    storage_opt: dict[str, str] | None = Body(
        None, description="Storage driver options"
    ),
    sysctls: dict[str, str] | None = Body(None, description="Sysctls options"),
    tmpfs: dict[str, str] | None = Body(None, description="Mount a tmpfs directory"),
    tty: bool | None = Body(None, description="Allocate a pseudo-TTY"),
    ulimits: list[dict[str, Any]] | None = Body(None, description="Ulimit options"),
    userns_mode: str | None = Body(None, description="User namespace to use"),
    uts_mode: str | None = Body(None, description="UTS mode to use"),
    volume_driver: str | None = Body(
        None, description="Optional volume driver for the container"
    ),
    volumes_from: list[str] | None = Body(
        None, description="Mount volumes from the specified container(s)"
    ),
) -> dict[str, Any]:
    """
    Run a container from an image.

    This endpoint creates and starts a container from the specified image.
    It can run the container in the background (detach=True) or wait for it to finish.
    The container can be automatically removed when it exits (remove=True).

    Example (run nginx in the background):
    ```JSON
    {
      "image_name": "nginx:latest",
      "detach": true
    }
    ```

    Example (run a command and wait for it to finish):
    ```JSON
    {
      "image_name": "alpine:latest",
      "command": ["echo", "Hello, World!"],
      "remove": true
    }
    ```

    Example (run with environment variables and volumes):
    ```JSON
    {
      "image_name": "postgres:13",
      "environment": {
        "POSTGRES_PASSWORD": "mysecretpassword"
      },
      "volumes": {
        "pgdata": {
          "bind": "/var/lib/postgresql/data",
          "mode": "rw"
        }
      }
    }
    ```
    """
    try:
        # Prepare kwargs for the run method
        kwargs: dict[str, Any] = {}

        # Add optional parameters if provided
        if container_name:
            kwargs["name"] = container_name
        if environment:
            kwargs["environment"] = environment
        if volumes:
            kwargs["volumes"] = volumes
        if detach:
            kwargs["detach"] = detach
        if auto_remove:
            kwargs["auto_remove"] = auto_remove
        if privileged:
            kwargs["privileged"] = privileged
        if network:
            kwargs["network"] = network
        if ports:
            kwargs["ports"] = ports
        if user:
            kwargs["user"] = user
        if working_dir:
            kwargs["working_dir"] = working_dir
        if entrypoint:
            kwargs["entrypoint"] = entrypoint
        if cap_add:
            kwargs["cap_add"] = cap_add
        if cap_drop:
            kwargs["cap_drop"] = cap_drop
        if device_cgroup_rules:
            kwargs["device_cgroup_rules"] = device_cgroup_rules
        if devices:
            kwargs["devices"] = devices
        if dns:
            kwargs["dns"] = dns
        if dns_search:
            kwargs["dns_search"] = dns_search
        if extra_hosts:
            kwargs["extra_hosts"] = extra_hosts
        if group_add:
            kwargs["group_add"] = group_add
        if init is not None:
            kwargs["init"] = init
        if ipc_mode:
            kwargs["ipc_mode"] = ipc_mode
        if isolation:
            kwargs["isolation"] = isolation
        if labels:
            kwargs["labels"] = labels
        if log_driver:
            kwargs["log_driver"] = log_driver
        if log_options:
            kwargs["log_options"] = log_options
        if mac_address:
            kwargs["mac_address"] = mac_address
        if mem_limit:
            kwargs["mem_limit"] = mem_limit
        if mem_reservation:
            kwargs["mem_reservation"] = mem_reservation
        if memswap_limit:
            kwargs["memswap_limit"] = memswap_limit
        if oom_kill_disable is not None:
            kwargs["oom_kill_disable"] = oom_kill_disable
        if oom_score_adj is not None:
            kwargs["oom_score_adj"] = oom_score_adj
        if pid_mode:
            kwargs["pid_mode"] = pid_mode
        if pids_limit is not None:
            kwargs["pids_limit"] = pids_limit
        if platform:
            kwargs["platform"] = platform
        if restart_policy:
            kwargs["restart_policy"] = restart_policy
        if security_opt:
            kwargs["security_opt"] = security_opt
        if shm_size:
            kwargs["shm_size"] = shm_size
        if stdin_open is not None:
            kwargs["stdin_open"] = stdin_open
        if stop_signal:
            kwargs["stop_signal"] = stop_signal
        if stop_timeout is not None:
            kwargs["stop_timeout"] = stop_timeout
        if storage_opt:
            kwargs["storage_opt"] = storage_opt
        if sysctls:
            kwargs["sysctls"] = sysctls
        if tmpfs:
            kwargs["tmpfs"] = tmpfs
        if tty is not None:
            kwargs["tty"] = tty
        if ulimits:
            kwargs["ulimits"] = ulimits
        if userns_mode:
            kwargs["userns_mode"] = userns_mode
        if uts_mode:
            kwargs["uts_mode"] = uts_mode
        if volume_driver:
            kwargs["volume_driver"] = volume_driver
        if volumes_from:
            kwargs["volumes_from"] = volumes_from

        # Run the container
        result = podman_client.containers.run(
            image=image_name, command=command, remove=remove, **kwargs
        )

        # If detach is True, result is a Container object
        if detach:
            # Check if result has the required attributes (id and name)
            # This works with both real Container objects and mocks in tests
            if hasattr(result, "id") and hasattr(result, "name"):
                return {
                    "status": "success",
                    "message": f"Container started from image {image_name}",
                    "container_id": result.id,
                    "container_name": result.name,
                }
            else:
                # This should not happen if detach=True, but handle it just in case
                return {
                    "status": "success",
                    "message": f"Container started from image {image_name}",
                }

        # For non-detached containers, result is either bytes, str, or an iterator
        output: str = ""

        # If result is bytes, decode it
        if isinstance(result, bytes):
            output = result.decode("utf-8")
        # If result is a string, use it directly
        elif isinstance(result, str):
            output = result
        # If result is an iterator, join the items
        elif hasattr(result, "__iter__") and not isinstance(result, (str, bytes)):
            # Join the iterator items into a string
            output_parts = []
            for item in result:
                if isinstance(item, bytes):
                    output_parts.append(item.decode("utf-8"))
                else:
                    output_parts.append(str(item))
            output = "".join(output_parts)
        # Fallback for any other type
        else:
            output = str(result)

        return {
            "status": "success",
            "message": f"Container from image {image_name} completed",
            "output": output,
        }

    except ImageNotFound:
        raise HTTPException(status_code=404, detail=f"Image {image_name} not found")
    except ContainerError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Container error: {str(e)}. Exit code: {e.exit_status}",
        )
    except APIError as e:
        raise HTTPException(
            status_code=500, detail=f"Error running container: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.delete("/{container_id}", status_code=204)
def delete_container(
    container_id: str,
    podman_client: Annotated[PodmanClient, Depends(get_podman_client)],
    force: bool = Query(False, description="Force removal of a running container"),
) -> None:
    """
    Delete a container by ID or name.

    If the container is running, use `force=true` to forcibly remove it.

    Returns:
        HTTP 204 No Content on success.
    """
    try:
        container = podman_client.containers.get(container_id)
        container.remove(force=force)
    except NotFound:
        raise HTTPException(
            status_code=404, detail=f"Container {container_id} not found"
        )
    except APIError as e:
        logger.exception("Error deleting container")
        if e.status_code == 409:
            raise HTTPException(status_code=409, detail=e.explanation)
        raise HTTPException(
            status_code=500,
            detail="Error deleting container. Consider using force=True.",
        )
    except Exception:
        logger.exception("Unexpected error while deleting container")
        raise HTTPException(status_code=500, detail="Unexpected error")
