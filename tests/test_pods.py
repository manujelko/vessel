from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from podman.errors import APIError, NotFound
from requests.models import Response

from app.dependencies import get_podman_client
from app.main import app

client = TestClient(app)


def test_list_pods_success():
    mock_pod1 = MagicMock()
    mock_pod1.attrs = {"Name": "pod1"}
    mock_pod2 = MagicMock()
    mock_pod2.attrs = {"Name": "pod2"}

    mock_client = MagicMock()
    mock_client.pods.list.return_value = [mock_pod1, mock_pod2]

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/pods")
        assert response.status_code == 200
        assert response.json() == [{"Name": "pod1"}, {"Name": "pod2"}]
        mock_client.pods.list.assert_called_once_with(all=False)
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_list_pods_api_error():
    mock_client = MagicMock()
    mock_client.pods.list.side_effect = APIError("fail")

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/pods")
        assert response.status_code == 500
        assert "Failed to list pods" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_inspect_pod_success():
    mock_pod = MagicMock()
    mock_pod.attrs = {"Name": "pod1"}

    mock_client = MagicMock()
    mock_client.pods.get.return_value = mock_pod

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/pods/pod1")
        assert response.status_code == 200
        assert response.json() == {"Name": "pod1"}
        mock_client.pods.get.assert_called_with("pod1")
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_inspect_pod_not_found():
    mock_client = MagicMock()
    mock_client.pods.get.side_effect = NotFound("not found")

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/pods/ghost")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_inspect_pod_api_error():
    mock_client = MagicMock()
    mock_client.pods.get.side_effect = APIError("boom")

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/pods/panic")
        assert response.status_code == 500
        assert "Failed to inspect pod" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_create_pod_success():
    mock_pod = MagicMock()
    mock_pod.attrs = {"Name": "mypod"}

    mock_client = MagicMock()
    mock_client.pods.create.return_value = mock_pod

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.post("/api/pods", json={"name": "mypod"})
        assert response.status_code == 201
        assert response.json() == {"Name": "mypod"}
        mock_client.pods.create.assert_called_with(
            name="mypod", labels={}, ports=[], share=None
        )
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_create_pod_api_error():
    mock_client = MagicMock()
    mock_client.pods.create.side_effect = APIError("bad create")

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.post("/api/pods", json={"name": "fail"})
        assert response.status_code == 500
        assert "Failed to create pod" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_pod_success():
    mock_pod = MagicMock()
    mock_client = MagicMock()
    mock_client.pods.get.return_value = mock_pod

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/pods/mypod")
        assert response.status_code == 204
        mock_pod.remove.assert_called_with(force=False)
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_pod_force():
    mock_pod = MagicMock()
    mock_client = MagicMock()
    mock_client.pods.get.return_value = mock_pod

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/pods/mypod?force=true")
        assert response.status_code == 204
        mock_pod.remove.assert_called_with(force=True)
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_pod_not_found():
    mock_client = MagicMock()
    mock_client.pods.get.side_effect = NotFound("not found")

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/pods/missing")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_pod_conflict():
    mock_pod = MagicMock()
    response_ = Response()
    response_.status_code = 409
    error = APIError("conflict", response=response_, explanation="Pod is in use")
    mock_pod.remove.side_effect = error

    mock_client = MagicMock()
    mock_client.pods.get.return_value = mock_pod

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/pods/locked")
        assert response.status_code == 409
        assert "Pod is in use" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)


def test_delete_pod_api_error():
    mock_pod = MagicMock()
    mock_pod.remove.side_effect = APIError("fail")

    mock_client = MagicMock()
    mock_client.pods.get.return_value = mock_pod

    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.delete("/api/pods/broken")
        assert response.status_code == 500
        assert "Failed to delete pod" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_podman_client)
