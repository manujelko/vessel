from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from podman.errors import APIError, ContainerError, ImageNotFound, NotFound
from requests.models import Response

from app.dependencies import get_podman_client
from app.main import app

client = TestClient(app)


def test_list_containers() -> None:
    # Create mock container objects
    mock_container1 = MagicMock()
    mock_container1.attrs = {
        "id": "container123",
        "name": "test-container-1",
        "image": "nginx:latest",
        "status": "running",
        "created": "2023-01-01T00:00:00Z",
        "labels": {"app": "web"},
    }

    mock_container2 = MagicMock()
    mock_container2.attrs = {
        "id": "container456",
        "name": "test-container-2",
        "image": "alpine:latest",
        "status": "exited",
        "created": "2023-01-02T00:00:00Z",
        "labels": {"app": "util"},
    }

    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.containers = MagicMock()
    mock_client.containers.list.return_value = [mock_container1, mock_container2]

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.get("/api/containers?all=true")

        # Verify the response
        assert response.status_code == 200
        containers = response.json()
        assert len(containers) == 2

        # Verify the first container
        assert containers[0]["id"] == "container123"
        assert containers[0]["name"] == "test-container-1"
        assert containers[0]["image"] == "nginx:latest"
        assert containers[0]["status"] == "running"
        assert containers[0]["created"] == "2023-01-01T00:00:00Z"
        assert containers[0]["labels"] == {"app": "web"}

        # Verify the second container
        assert containers[1]["id"] == "container456"
        assert containers[1]["name"] == "test-container-2"
        assert containers[1]["image"] == "alpine:latest"
        assert containers[1]["status"] == "exited"
        assert containers[1]["created"] == "2023-01-02T00:00:00Z"
        assert containers[1]["labels"] == {"app": "util"}

        # Verify that the mock was called correctly
        mock_client.containers.list.assert_called_with(
            all=True, since=None, before=None, limit=0, filters={}
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_list_containers_with_limit() -> None:
    # Create mock container objects
    mock_container = MagicMock()
    mock_container.attrs = {
        "id": "container123",
        "name": "test-container",
        "image": "nginx:latest",
        "status": "running",
        "created": "2023-01-01T00:00:00Z",
        "labels": {"app": "web"},
    }

    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.containers = MagicMock()
    mock_client.containers.list.return_value = [mock_container]

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint with limit parameter
        response = client.get("/api/containers?limit=1")

        # Verify the response
        assert response.status_code == 200
        containers = response.json()
        assert len(containers) == 1

        # Verify the container details
        assert containers[0]["id"] == "container123"
        assert containers[0]["name"] == "test-container"

        # Verify that the mock was called correctly with limit parameter
        mock_client.containers.list.assert_called_with(
            all=False, since=None, limit=1, before=None, filters={}
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_list_containers_with_filters() -> None:
    # Create mock container objects
    mock_container = MagicMock()
    mock_container.attrs = {
        "id": "container123",
        "name": "test-container",
        "image": "nginx:latest",
        "status": "running",
        "created": "2023-01-01T00:00:00Z",
        "labels": {"app": "web"},
    }

    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.containers = MagicMock()
    mock_client.containers.list.return_value = [mock_container]

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint with status filter
        response = client.get("/api/containers?status=running")

        # Verify the response
        assert response.status_code == 200
        containers = response.json()
        assert len(containers) == 1

        # Verify the container details
        assert containers[0]["id"] == "container123"
        assert containers[0]["status"] == "running"

        # Verify that the mock was called correctly with filters parameter
        mock_client.containers.list.assert_called_with(
            all=False, since=None, before=None, limit=0, filters={"status": "running"}
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_list_containers_empty() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.containers = MagicMock()
    mock_client.containers.list.return_value = []

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.get("/api/containers")

        # Verify the response
        assert response.status_code == 200
        containers = response.json()
        assert len(containers) == 0
        assert containers == []

        # Verify that the mock was called correctly
        mock_client.containers.list.assert_called_with(
            all=False, since=None, before=None, limit=0, filters={}
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_list_containers_api_error() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.containers = MagicMock()
    mock_client.containers.list.side_effect = APIError("API Error")

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.get("/api/containers")

        # Verify the response
        assert response.status_code == 500
        assert "Error listing containers" in response.json()["detail"]

        # Verify that the mock was called correctly
        mock_client.containers.list.assert_called_with(
            all=False, since=None, before=None, limit=0, filters={}
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_run_container_detached() -> None:
    # Create a mock for the Container object
    mock_container = MagicMock()
    mock_container.id = "container123"
    mock_container.name = "test-container"

    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.containers.run.return_value = mock_container

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/containers",
            json={
                "image_name": "nginx:latest",
                "detach": True,
                "container_name": "test-container",
            },
        )

        # Verify the response
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "Container started from image nginx:latest",
            "container_id": "container123",
            "container_name": "test-container",
        }

        # Verify that the mock was called correctly
        mock_client.containers.run.assert_called_with(
            image="nginx:latest",
            command=None,
            remove=False,
            name="test-container",
            detach=True,
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_run_container_with_command() -> None:
    # Create a mock for the container output
    mock_output = b"Hello, World!"

    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.containers.run.return_value = mock_output

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/containers",
            json={
                "image_name": "alpine:latest",
                "command": ["echo", "Hello, World!"],
                "remove": True,
            },
        )

        # Verify the response
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "Container from image alpine:latest completed",
            "output": "Hello, World!",
        }

        # Verify that the mock was called correctly
        mock_client.containers.run.assert_called_with(
            image="alpine:latest",
            command=["echo", "Hello, World!"],
            remove=True,
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_run_container_with_environment_and_volumes() -> None:
    # Create a mock for the container output
    mock_output = b"Container started"

    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.containers.run.return_value = mock_output

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/containers",
            json={
                "image_name": "postgres:13",
                "environment": {"POSTGRES_PASSWORD": "mysecretpassword"},
                "volumes": {
                    "pgdata": {"bind": "/var/lib/postgresql/data", "mode": "rw"}
                },
            },
        )

        # Verify the response
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "Container from image postgres:13 completed",
            "output": "Container started",
        }

        # Verify that the mock was called correctly
        mock_client.containers.run.assert_called_with(
            image="postgres:13",
            command=None,
            remove=False,
            environment={"POSTGRES_PASSWORD": "mysecretpassword"},
            volumes={"pgdata": {"bind": "/var/lib/postgresql/data", "mode": "rw"}},
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_run_container_image_not_found() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.containers.run.side_effect = ImageNotFound("Image not found")

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/containers",
            json={
                "image_name": "nonexistent:latest",
            },
        )

        # Verify the response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

        # Verify that the mock was called correctly
        mock_client.containers.run.assert_called_with(
            image="nonexistent:latest",
            command=None,
            remove=False,
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_run_container_error() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()

    # Create a mock container for the error
    mock_container = MagicMock()
    mock_container.id = "container123"

    # Create a ContainerError with the mock container
    container_error = ContainerError(
        container=mock_container,
        exit_status=1,
        command=["echo", "test"],
        image="alpine:latest",
    )

    mock_client.containers.run.side_effect = container_error

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/containers",
            json={
                "image_name": "alpine:latest",
                "command": ["echo", "test"],
            },
        )

        # Verify the response
        assert response.status_code == 500
        assert "Container error" in response.json()["detail"]
        assert "Exit code: 1" in response.json()["detail"]

        # Verify that the mock was called correctly
        mock_client.containers.run.assert_called_with(
            image="alpine:latest",
            command=["echo", "test"],
            remove=False,
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_run_container_api_error() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.containers.run.side_effect = APIError("API Error")

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/containers",
            json={
                "image_name": "nginx:latest",
            },
        )

        # Verify the response
        assert response.status_code == 500
        assert "Error running container" in response.json()["detail"]

        # Verify that the mock was called correctly
        mock_client.containers.run.assert_called_with(
            image="nginx:latest",
            command=None,
            remove=False,
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_run_container_with_all_options() -> None:
    # Create a mock for the Container object
    mock_container = MagicMock()
    mock_container.id = "container456"
    mock_container.name = "full-options-container"

    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.containers.run.return_value = mock_container

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint with many options
        response = client.post(
            "/api/containers",
            json={
                "image_name": "nginx:latest",
                "container_name": "full-options-container",
                "detach": True,
                "environment": {"ENV_VAR": "value"},
                "volumes": {"vol1": {"bind": "/mnt", "mode": "rw"}},
                "ports": {"80/tcp": 8080},
                "user": "nginx",
                "working_dir": "/app",
                "entrypoint": ["/bin/sh", "-c"],
                "command": ["nginx", "-g", "daemon off;"],
                "privileged": True,
                "network": "host",
                "labels": {"com.example.label": "value"},
                "mem_limit": "512m",
                "restart_policy": {"Name": "always"},
            },
        )

        # Verify the response
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "Container started from image nginx:latest",
            "container_id": "container456",
            "container_name": "full-options-container",
        }

        # Verify that the mock was called with all the options
        mock_client.containers.run.assert_called_once()
        call_args = mock_client.containers.run.call_args[1]

        assert call_args["image"] == "nginx:latest"
        assert call_args["command"] == ["nginx", "-g", "daemon off;"]
        assert call_args["name"] == "full-options-container"
        assert call_args["detach"] is True
        assert call_args["environment"] == {"ENV_VAR": "value"}
        assert call_args["volumes"] == {"vol1": {"bind": "/mnt", "mode": "rw"}}
        assert call_args["ports"] == {"80/tcp": 8080}
        assert call_args["user"] == "nginx"
        assert call_args["working_dir"] == "/app"
        assert call_args["entrypoint"] == ["/bin/sh", "-c"]
        assert call_args["privileged"] is True
        assert call_args["network"] == "host"
        assert call_args["labels"] == {"com.example.label": "value"}
        assert call_args["mem_limit"] == "512m"
        assert call_args["restart_policy"] == {"Name": "always"}
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_delete_container_success():
    container = MagicMock()
    container.remove.return_value = None

    mock_client = MagicMock()
    mock_client.containers.get.return_value = container

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/containers/mycontainer")
        assert response.status_code == 204
        container.remove.assert_called_once_with(force=False)
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_container_force():
    container = MagicMock()
    container.remove.return_value = None

    mock_client = MagicMock()
    mock_client.containers.get.return_value = container

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/containers/mycontainer?force=true")
        assert response.status_code == 204
        container.remove.assert_called_once_with(force=True)
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_container_not_found():
    mock_client = MagicMock()
    mock_client.containers.get.side_effect = NotFound("not found")

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/containers/missing")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_container_conflict():
    container = MagicMock()
    response_ = Response()
    response_.status_code = 409
    error = APIError("conflict", response=response_, explanation="Container is in use")
    container.remove.side_effect = error

    mock_client = MagicMock()
    mock_client.containers.get.return_value = container

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/containers/locked")
        assert response.status_code == 409
        assert "Container is in use" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_container_api_error():
    container = MagicMock()
    container.remove.side_effect = APIError("server error")

    mock_client = MagicMock()
    mock_client.containers.get.return_value = container

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/containers/broken")
        assert response.status_code == 500
        assert "Error deleting container" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_container_unexpected_exception():
    container = MagicMock()
    container.remove.side_effect = Exception("unexpected")

    mock_client = MagicMock()
    mock_client.containers.get.return_value = container

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/containers/error")
        assert response.status_code == 500
        assert "Unexpected error" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)
