from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from podman.errors import APIError, ImageNotFound

from app.main import app
from app.dependencies import get_podman_client

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

    # Expected response - a list of strings identifying each image
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


def test_pull_image_success_with_auth() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.login.return_value = {"Status": "Login Succeeded"}
    mock_client.images.pull.return_value = {"Id": "image1", "Names": ["nginx:latest"]}

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/images/pull",
            json={
                "repository": "nginx",
                "tag": "latest",
                "registry": "docker.io",
                "username": "testuser",
                "password": "testpass",
            },
        )

        # Verify the response
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "Image nginx:latest pulled successfully",
        }

        # Verify that the mock methods were called correctly
        mock_client.login.assert_called_with(
            username="testuser", password="testpass", registry="docker.io"
        )
        mock_client.images.pull.assert_called_with(
            repository="docker.io/nginx",
            tag="latest",
            auth_config={"username": "testuser", "password": "testpass"},
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_pull_image_success_without_auth() -> None:
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
                "repository": "nginx",
                "tag": "latest",
            },
        )

        # Verify the response
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "Image nginx:latest pulled successfully",
        }

        # Verify that login was not called and pull was called without auth_config
        mock_client.login.assert_not_called()
        mock_client.images.pull.assert_called_with(
            repository="nginx", tag="latest", auth_config=None
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_pull_image_not_found() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.login.return_value = {"Status": "Login Succeeded"}
    mock_client.images.pull.side_effect = ImageNotFound("Image not found")

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/images/pull",
            json={
                "repository": "nonexistent",
                "tag": "latest",
                "registry": "docker.io",
                "username": "testuser",
                "password": "testpass",
            },
        )

        # Verify the response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

        # Verify that the mock methods were called correctly
        mock_client.login.assert_called_with(
            username="testuser", password="testpass", registry="docker.io"
        )
        mock_client.images.pull.assert_called_with(
            repository="docker.io/nonexistent",
            tag="latest",
            auth_config={"username": "testuser", "password": "testpass"},
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_pull_image_api_error() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.login.return_value = {"Status": "Login Succeeded"}
    mock_client.images.pull.side_effect = APIError("API Error")

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/images/pull",
            json={
                "repository": "nginx",
                "tag": "latest",
                "registry": "docker.io",
                "username": "testuser",
                "password": "testpass",
            },
        )

        # Verify the response
        assert response.status_code == 500
        assert "Error pulling image" in response.json()["detail"]

        # Verify that the mock methods were called correctly
        mock_client.login.assert_called_with(
            username="testuser", password="testpass", registry="docker.io"
        )
        mock_client.images.pull.assert_called_with(
            repository="docker.io/nginx",
            tag="latest",
            auth_config={"username": "testuser", "password": "testpass"},
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_pull_image_custom_registry_without_auth() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.images.pull.return_value = {"Id": "image1", "Names": ["myapp:latest"]}

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/images/pull",
            json={
                "repository": "myapp",
                "tag": "latest",
                "registry": "registry.example.com",
            },
        )

        # Verify the response
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "Image myapp:latest pulled successfully",
        }

        # Verify that login was not called and pull was called with the correct repository
        mock_client.login.assert_not_called()
        mock_client.images.pull.assert_called_with(
            repository="registry.example.com/myapp", tag="latest", auth_config=None
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_pull_image_login_error() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.login.side_effect = APIError("Invalid credentials")

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/images/pull",
            json={
                "repository": "nginx",
                "tag": "latest",
                "registry": "docker.io",
                "username": "testuser",
                "password": "testpass",
            },
        )

        # Verify the response
        assert response.status_code == 500
        assert "Error pulling image" in response.json()["detail"]

        # Verify that login was attempted but pull was not called (since login failed)
        mock_client.login.assert_called_with(
            username="testuser", password="testpass", registry="docker.io"
        )
        mock_client.images.pull.assert_not_called()
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)
