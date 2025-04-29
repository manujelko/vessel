from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from podman.errors import APIError

from app.dependencies import get_podman_client
from app.main import app

client = TestClient(app)


def test_login_repository_success() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.login.return_value = {"Status": "Login Succeeded"}

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/login/repository",
            json={
                "username": "testuser",
                "password": "testpass",
                "registry": "docker.io",
            },
        )

        # Verify the response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "Successfully logged in to docker.io" in response.json()["message"]
        assert response.json()["details"] == {"Status": "Login Succeeded"}

        # Verify that the mock methods were called correctly
        mock_client.login.assert_called_with(
            username="testuser", password="testpass", registry="docker.io"
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_login_repository_default_registry() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.login.return_value = {"Status": "Login Succeeded"}

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint without specifying registry
        response = client.post(
            "/api/login/repository",
            json={
                "username": "testuser",
                "password": "testpass",
            },
        )

        # Verify the response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "Successfully logged in to docker.io" in response.json()["message"]

        # Verify that the mock methods were called correctly with default registry
        mock_client.login.assert_called_with(
            username="testuser", password="testpass", registry="docker.io"
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)


def test_login_repository_error() -> None:
    # Create a mock for the Podman client
    mock_client = MagicMock()
    mock_client.login.side_effect = APIError("Invalid credentials")

    # Override the dependency to use our mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client

    try:
        # Make the request to the endpoint
        response = client.post(
            "/api/login/repository",
            json={
                "username": "testuser",
                "password": "wrongpass",
                "registry": "docker.io",
            },
        )

        # Verify the response
        assert response.status_code == 401
        assert "Authentication failed" in response.json()["detail"]

        # Verify that the mock methods were called correctly
        mock_client.login.assert_called_with(
            username="testuser", password="wrongpass", registry="docker.io"
        )
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)
