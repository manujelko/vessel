from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_podman_client

client = TestClient(app)


def test_get_images():
    # Create a mock for the images that will be returned
    mock_images = [
        {"Id": "image1", "Names": ["image1:latest"]},
        {"Id": "image2", "Names": ["image2:latest"]},
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
        assert response.json() == mock_images

        # Verify that the mock was called correctly
        mock_client.images.list.assert_called_once()
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_podman_client)
