from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from podman.errors import APIError, NotFound

from app.dependencies import get_podman_client
from app.main import app

client = TestClient(app)


def test_list_volumes_success():
    mock_volume1 = MagicMock()
    mock_volume1.attrs = {"Name": "vol1"}
    mock_volume2 = MagicMock()
    mock_volume2.attrs = {"Name": "vol2"}

    mock_client = MagicMock()
    mock_client.volumes.list.return_value = [mock_volume1, mock_volume2]

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/volumes")
        assert response.status_code == 200
        assert response.json() == [{"Name": "vol1"}, {"Name": "vol2"}]
        mock_client.volumes.list.assert_called_once()
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_list_volumes_api_error():
    mock_client = MagicMock()
    mock_client.volumes.list.side_effect = APIError("failed")

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/volumes")
        assert response.status_code == 500
        assert "Failed to list volumes" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_create_volume_success():
    mock_volume = MagicMock()
    mock_volume.attrs = {"Name": "myvolume"}

    mock_client = MagicMock()
    mock_client.volumes.create.return_value = mock_volume

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.post("/api/volumes", json={"name": "myvolume"})
        assert response.status_code == 201
        assert response.json() == {"Name": "myvolume"}
        mock_client.volumes.create.assert_called_with(
            name="myvolume", driver="local", labels={}, options={}
        )
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_create_volume_api_error():
    mock_client = MagicMock()
    mock_client.volumes.create.side_effect = APIError("failed")

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.post("/api/volumes", json={"name": "fail"})
        assert response.status_code == 500
        assert "Failed to create volume" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_inspect_volume_success():
    mock_volume = MagicMock()
    mock_volume.attrs = {"Name": "vol1"}

    mock_client = MagicMock()
    mock_client.volumes.get.return_value = mock_volume

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/volumes/vol1")
        assert response.status_code == 200
        assert response.json() == {"Name": "vol1"}
        mock_client.volumes.get.assert_called_with("vol1")
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_inspect_volume_not_found():
    mock_client = MagicMock()
    mock_client.volumes.get.side_effect = NotFound("not found")

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/volumes/missing")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_inspect_volume_api_error():
    mock_client = MagicMock()
    mock_client.volumes.get.side_effect = APIError("broken")

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/volumes/broken")
        assert response.status_code == 500
        assert "Failed to inspect volume" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_volume_success():
    mock_volume = MagicMock()
    mock_client = MagicMock()
    mock_client.volumes.get.return_value = mock_volume

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/volumes/vol1")
        assert response.status_code == 204
        mock_volume.remove.assert_called_with(force=False)
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_volume_force():
    mock_volume = MagicMock()
    mock_client = MagicMock()
    mock_client.volumes.get.return_value = mock_volume

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/volumes/vol1?force=true")
        assert response.status_code == 204
        mock_volume.remove.assert_called_with(force=True)
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_volume_not_found():
    mock_client = MagicMock()
    mock_client.volumes.get.side_effect = NotFound("not found")

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/volumes/missing")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_volume_conflict():
    from requests.models import Response

    response_ = Response()
    response_.status_code = 409
    err = APIError("conflict", response=response_, explanation="Volume is in use")

    mock_volume = MagicMock()
    mock_volume.remove.side_effect = err
    mock_client = MagicMock()
    mock_client.volumes.get.return_value = mock_volume

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/volumes/locked")
        assert response.status_code == 409
        assert "Volume is in use" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_volume_api_error():
    mock_volume = MagicMock()
    mock_volume.remove.side_effect = APIError("fail")

    mock_client = MagicMock()
    mock_client.volumes.get.return_value = mock_volume

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/volumes/broken")
        assert response.status_code == 500
        assert "Failed to delete volume" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)
