from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from podman.errors import APIError, ImageNotFound

from app.dependencies import get_podman_client
from app.main import app

client = TestClient(app)


def test_get_images() -> None:
    # Create mock image objects with tags property
    mock_image1 = MagicMock()
    mock_image1.tags = ["registry.example.com/image1:latest"]
    mock_image1.id = "image1_id"

    mock_image2 = MagicMock()
    mock_image2.tags = [
        "registry.example.com/image2:v1.0",
        "registry.example.com/image2:latest",
    ]
    mock_image2.id = "image2_id"

    mock_image3 = MagicMock()
    mock_image3.tags = []
    mock_image3.id = "image3_id"

    mock_images = [mock_image1, mock_image2, mock_image3]

    # Expected response - a list of image names
    expected_response = [
        "registry.example.com/image1:latest",
        "registry.example.com/image2:v1.0",
        "registry.example.com/image2:latest",
        "image3_id",
    ]

    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.images.list.return_value = mock_images

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.get("/api/images")

        # Verify the response
        assert response.status_code == 200
        assert response.json() == expected_response

        # Verify that the mock was called correctly
        mock_client.images.list.assert_called_once()
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_pull_image_success() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.images.pull.return_value = {"Id": "image1", "Names": ["nginx:latest"]}

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/images/pull",
            json={
                "image_name": "nginx:latest",
            },
        )

        # Verify the response
        assert response.status_code == 204
        assert response.content == b""  # Empty response body

        # Verify that the mock methods were called correctly
        mock_client.images.pull.assert_called_with("nginx:latest")
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_pull_image_not_found() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.images.pull.side_effect = ImageNotFound("Image not found")

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/images/pull",
            json={
                "image_name": "nonexistent:latest",
            },
        )

        # Verify the response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

        # Verify that the mock methods were called correctly
        mock_client.images.pull.assert_called_with("nonexistent:latest")
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_pull_image_api_error() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.images.pull.side_effect = APIError("API Error")

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/images/pull",
            json={
                "image_name": "nginx:latest",
            },
        )

        # Verify the response
        assert response.status_code == 500
        assert "Error pulling image" in response.json()["detail"]

        # Verify that the mock methods were called correctly
        mock_client.images.pull.assert_called_with("nginx:latest")
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_pull_image_with_custom_registry() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.images.pull.return_value = {
        "Id": "image1",
        "Names": ["registry.example.com/myapp:latest"],
    }

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/images/pull",
            json={
                "image_name": "registry.example.com/myapp:latest",
            },
        )

        # Verify the response
        assert response.status_code == 204
        assert response.content == b""  # Empty response body

        # Verify that the mock methods were called correctly
        mock_client.images.pull.assert_called_with("registry.example.com/myapp:latest")
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_delete_image_success() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.images.remove.return_value = [
        {
            "Deleted": "sha256:a1801b843b1bfaf77c501e7a6d3f709401a1e0c83863037fa3aab063a7fdb9dc"
        },
        {"Untagged": "nginx:latest"},
        {"ExitCode": 0},
    ]

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    # Image name to delete
    image_name = "nginx:latest"

    try:
        # Make the request to the endpoint
        response = client.delete(f"/api/images/{image_name}")

        # Verify the response - should be 204 No Content with no body
        assert response.status_code == 204
        assert response.content == b""  # Empty response body

        # Verify that the mock was called correctly
        mock_client.images.remove.assert_called_with(image=image_name, force=False)
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_delete_image_force() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.images.remove.return_value = [
        {
            "Deleted": "sha256:a1801b843b1bfaf77c501e7a6d3f709401a1e0c83863037fa3aab063a7fdb9dc"
        },
        {"Untagged": "nginx:latest"},
        {"ExitCode": 0},
    ]

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    # Image name to delete
    image_name = "nginx:latest"

    try:
        # Make the request to the endpoint with force=true
        response = client.delete(f"/api/images/{image_name}?force=true")

        # Verify the response - should be 204 No Content with no body
        assert response.status_code == 204
        assert response.content == b""  # Empty response body

        # Verify that the mock was called correctly with force=True
        mock_client.images.remove.assert_called_with(image=image_name, force=True)
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_delete_image_not_found() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.images.remove.side_effect = ImageNotFound("Image not found")

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    # Nonexistent image name
    image_name = "nonexistent:latest"

    try:
        # Make the request to the endpoint
        response = client.delete(f"/api/images/{image_name}")

        # Verify the response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

        # Verify that the mock was called correctly
        mock_client.images.remove.assert_called_with(image=image_name, force=False)
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_delete_image_api_error() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.images.remove.side_effect = APIError("Cannot delete image in use")

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    # Image name that will cause an API error
    image_name = "nginx:latest"

    try:
        # Make the request to the endpoint
        response = client.delete(f"/api/images/{image_name}")

        # Verify the response
        assert response.status_code == 500
        assert "Error deleting image" in response.json()["detail"]

        # Verify that the mock was called correctly
        mock_client.images.remove.assert_called_with(image=image_name, force=False)
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_delete_image_with_url_encoded_name() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.images.remove.return_value = [
        {
            "Deleted": "sha256:a1801b843b1bfaf77c501e7a6d3f709401a1e0c83863037fa3aab063a7fdb9dc"
        },
        {"Untagged": "quay.io/podman/hello:latest"},
        {"ExitCode": 0},
    ]

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    # Image name with characters that need URL encoding
    image_name = "quay.io/podman/hello:latest"

    try:
        # Make the request to the endpoint
        # With the :path suffix in the route, FastAPI will handle the slashes correctly
        response = client.delete(f"/api/images/{image_name}")

        # Verify the response - should be 204 No Content with no body
        assert response.status_code == 204
        assert response.content == b""  # Empty response body

        # Verify that the mock was called correctly with the image name
        mock_client.images.remove.assert_called_with(image=image_name, force=False)
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)
