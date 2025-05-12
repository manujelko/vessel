from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from podman.errors import APIError, NotFound

from app.dependencies import get_podman_client
from app.main import app

client = TestClient(app)


def override_client(container_mock):
    mock_client = MagicMock()
    mock_client.containers.get.return_value = container_mock
    app.dependency_overrides[get_podman_client] = lambda: mock_client
    return mock_client


def clear_override():
    app.dependency_overrides.pop(get_podman_client, None)


def test_get_logs_json_string():
    container = MagicMock()
    container.logs.return_value = "log 1\nlog 2\n"
    override_client(container)
    try:
        response = client.get("/api/logs/abc123")
        assert response.status_code == 200
        assert response.json() == ["log 1", "log 2"]
    finally:
        clear_override()


def test_get_logs_json_bytes():
    container = MagicMock()
    container.logs.return_value = b"log 1\nlog 2\n"
    override_client(container)
    try:
        response = client.get("/api/logs/abc123")
        assert response.status_code == 200
        assert response.json() == ["log 1", "log 2"]
    finally:
        clear_override()


def test_get_logs_json_iterator():
    container = MagicMock()
    container.logs.return_value = iter([b"log 1\n", b"log 2\n"])
    override_client(container)
    try:
        response = client.get("/api/logs/abc123")
        assert response.status_code == 200
        assert response.json() == ["log 1", "log 2"]
    finally:
        clear_override()


def test_get_logs_not_found():
    mock_client = MagicMock()
    mock_client.containers.get.side_effect = NotFound("not found")
    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/logs/missing")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    finally:
        clear_override()


def test_get_logs_api_error():
    mock_client = MagicMock()
    mock_client.containers.get.side_effect = APIError("bad request")
    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/logs/broken")
        assert response.status_code == 500
        assert response.json()["detail"] == "Error fetching logs"
    finally:
        clear_override()


def test_get_logs_unexpected_exception():
    mock_client = MagicMock()
    mock_client.containers.get.side_effect = Exception("unexpected")
    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/logs/fail")
        assert response.status_code == 500
        assert response.json()["detail"] == "Unexpected error"
    finally:
        clear_override()


def test_stream_logs():
    container = MagicMock()
    container.logs.return_value = iter([b"stream 1\n", b"stream 2\n"])
    _ = override_client(container)

    try:
        response = client.get("/api/logs/abc123/stream")
        assert response.status_code == 200
        assert "stream 1\n" in response.text
        assert "stream 2\n" in response.text
        container.logs.assert_called_once_with(
            stream=True, stdout=True, stderr=True, since=None, tail=None
        )
    finally:
        clear_override()


def test_stream_logs_with_tail_and_since():
    container = MagicMock()
    container.logs.return_value = iter([b"line A\n", b"line B\n"])
    _ = override_client(container)

    try:
        response = client.get(
            "/api/logs/abc123/stream?tail=100&since=2024-01-01T00:00:00Z&stdout=false&stderr=true"
        )
        assert response.status_code == 200
        assert "line A\n" in response.text
        assert "line B\n" in response.text

        container.logs.assert_called_once_with(
            stream=True,
            stdout=False,
            stderr=True,
            since="2024-01-01T00:00:00Z",
            tail="100",
        )
    finally:
        clear_override()


def test_stream_logs_not_found():
    mock_client = MagicMock()
    mock_client.containers.get.side_effect = NotFound("not found")
    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/logs/missing/stream")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    finally:
        clear_override()


def test_stream_logs_api_error():
    mock_client = MagicMock()
    mock_client.containers.get.side_effect = APIError("bad request")
    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/logs/broken/stream")
        assert response.status_code == 500
        assert response.json()["detail"] == "Error streaming logs"
    finally:
        clear_override()


def test_stream_logs_unexpected_exception():
    mock_client = MagicMock()
    mock_client.containers.get.side_effect = Exception("unexpected")
    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/logs/fail/stream")
        assert response.status_code == 500
        assert response.json()["detail"] == "Unexpected error"
    finally:
        clear_override()
