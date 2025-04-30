import datetime as dt
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from podman.errors import APIError, ImageNotFound
from requests.models import Response

from app.dependencies import get_podman_client
from app.main import app
from app.models import Image

client = TestClient(app)


def test_get_images() -> None:
    # Create mock image objects with tags property
    mock_image1 = MagicMock()
    mock_image1.attrs = {
        "Arch": "arm64",
        "Containers": 4,
        "Created": 1716689914,
        "Digest": "sha256:41316c18917a27a359ee3191fd8f43559d30592f82a144bbc59d9d44790f6e7a",
        "History": ["quay.io/podman/hello:latest"],
        "Id": "83fc7ce1224f5ed3885f6aaec0bb001c0bbb2a308e3250d7408804a720c72a32",
        "IsManifestList": False,
        "Labels": {
            "artist": "Máirín Ní Ḋuḃṫaiġ, X/Twitter:@mairin",
            "io.buildah.version": "1.23.1",
            "io.containers.capabilities": "sys_chroot",
            "maintainer": "Podman Maintainers",
            "org.opencontainers.image.description": "Hello world image with ascii art",
            "org.opencontainers.image.documentation": "https://github.com/containers/PodmanHello/blob/76b262056eae09851d0a952d0f42b5bbeedde471/README.md",
            "org.opencontainers.image.revision": "76b262056eae09851d0a952d0f42b5bbeedde471",
            "org.opencontainers.image.source": "https://raw.githubusercontent.com/containers/PodmanHello/76b262056eae09851d0a952d0f42b5bbeedde471/Containerfile",
            "org.opencontainers.image.title": "hello image",
            "org.opencontainers.image.url": "https://github.com/containers/PodmanHello/actions/runs/9239934617",
        },
        "Names": ["quay.io/podman/hello:latest"],
        "Os": "linux",
        "ParentId": "",
        "RepoDigests": [
            "quay.io/podman/hello@sha256:41316c18917a27a359ee3191fd8f43559d30592f82a144bbc59d9d44790f6e7a",
            "quay.io/podman/hello@sha256:5c44ef36dc5e35a76904da0e028cf9413e0176a653525162368af13fed03571c",
        ],
        "RepoTags": ["quay.io/podman/hello:latest"],
        "SharedSize": 0,
        "Size": 579593,
        "VirtualSize": 579593,
    }

    mock_image2 = MagicMock()
    mock_image2.attrs = {
        "Arch": "arm64",
        "Containers": 0,
        "Created": 1624422849,
        "Digest": "sha256:47ae43cdfc7064d28800bc42e79a429540c7c80168e8c8952778c0d5af1c09db",
        "History": ["docker.io/library/nginx:1.21.0"],
        "Id": "d868a2ccd9b148b984a40e49ab0b16e1434d5bca8f0bf8f2714ce7352c3d4555",
        "IsManifestList": False,
        "Labels": {"maintainer": "NGINX Docker Maintainers <docker-maint@nginx.com>"},
        "Names": ["docker.io/library/nginx:1.21.0"],
        "Os": "linux",
        "ParentId": "",
        "RepoDigests": [
            "docker.io/library/nginx@sha256:47ae43cdfc7064d28800bc42e79a429540c7c80168e8c8952778c0d5af1c09db",
            "docker.io/library/nginx@sha256:7c91baa42a9371c925b909701b84ee543aa2d6e9fda4543225af2e17f531a243",
        ],
        "RepoTags": ["docker.io/library/nginx:1.21.0"],
        "SharedSize": 0,
        "Size": 130092990,
        "VirtualSize": 130092990,
    }

    mock_images = [mock_image1, mock_image2]

    # Expected response - a list of image names
    expected_image_model1 = Image(
        id="83fc7ce1224f5ed3885f6aaec0bb001c0bbb2a308e3250d7408804a720c72a32",
        parent_id="",
        repo_tags=["quay.io/podman/hello:latest"],
        repo_digests=None,
        created=dt.datetime(2024, 5, 26, 3, 18, 34),
        size=579593,
        shared_size=0,
        virtual_size=579593,
        labels={
            "artist": "Máirín Ní Ḋuḃṫaiġ, X/Twitter:@mairin",
            "io.buildah.version": "1.23.1",
            "io.containers.capabilities": "sys_chroot",
            "maintainer": "Podman Maintainers",
            "org.opencontainers.image.description": "Hello world image with ascii art",
            "org.opencontainers.image.documentation": "https://github.com/containers/PodmanHello/blob/76b262056eae09851d0a952d0f42b5bbeedde471/README.md",
            "org.opencontainers.image.revision": "76b262056eae09851d0a952d0f42b5bbeedde471",
            "org.opencontainers.image.source": "https://raw.githubusercontent.com/containers/PodmanHello/76b262056eae09851d0a952d0f42b5bbeedde471/Containerfile",
            "org.opencontainers.image.title": "hello image",
            "org.opencontainers.image.url": "https://github.com/containers/PodmanHello/actions/runs/9239934617",
        },
        containers=4,
        architecture="arm64",
        os="linux",
        digest="sha256:41316c18917a27a359ee3191fd8f43559d30592f82a144bbc59d9d44790f6e7a",
        history=["quay.io/podman/hello:latest"],
        is_manifest_list=False,
        names=["quay.io/podman/hello:latest"],
    )
    expected_image_model2 = Image(
        id="d868a2ccd9b148b984a40e49ab0b16e1434d5bca8f0bf8f2714ce7352c3d4555",
        parent_id="",
        repo_tags=["docker.io/library/nginx:1.21.0"],
        repo_digests=None,
        created=dt.datetime(2021, 6, 23, 5, 34, 9),
        size=130092990,
        shared_size=0,
        virtual_size=130092990,
        labels={"maintainer": "NGINX Docker Maintainers <docker-maint@nginx.com>"},
        containers=0,
        architecture="arm64",
        os="linux",
        digest="sha256:47ae43cdfc7064d28800bc42e79a429540c7c80168e8c8952778c0d5af1c09db",
        history=["docker.io/library/nginx:1.21.0"],
        is_manifest_list=False,
        names=["docker.io/library/nginx:1.21.0"],
    )
    expected_response = [
        expected_image_model1.model_dump(mode="json"),
        expected_image_model2.model_dump(mode="json"),
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


class TestPullImage:
    def test_success(self) -> None:
        # Create a mock for the Podman client
        mock_client = MagicMock()
        mock_client.images.pull.return_value = {
            "Id": "image1",
            "Names": ["nginx:latest"],
        }

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

    def test_not_found(self) -> None:
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

    def test_api_error(self) -> None:
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

    def test_with_custom_registry(self) -> None:
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
            mock_client.images.pull.assert_called_with(
                "registry.example.com/myapp:latest"
            )
        finally:
            # Clean up the dependency override
            app.dependency_overrides.pop(get_podman_client)


class TestDeleteImage:
    def test_no_args(self) -> None:
        mock_client = MagicMock()
        app.dependency_overrides[get_podman_client] = lambda: mock_client
        try:
            response = client.delete("/api/images")
            assert response.status_code == 400
            assert (
                "Either image_id or image_name must be provided"
                == response.json()["detail"]
            )
        finally:
            app.dependency_overrides.pop(get_podman_client)

    def test_args_conflict(self) -> None:
        mock_client = MagicMock()
        app.dependency_overrides[get_podman_client] = lambda: mock_client
        try:
            response = client.delete("/api/images?image_id=123&image_name=456")
            assert response.status_code == 400
            assert (
                "Either image_id or image_name must be provided, not both"
                == response.json()["detail"]
            )
        finally:
            app.dependency_overrides.pop(get_podman_client)

    def test_by_name_success(self) -> None:
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
            response = client.delete(f"/api/images/?image_name={image_name}")

            # Verify the response - should be 204 No Content with no body
            assert response.status_code == 204
            assert response.content == b""  # Empty response body

            # Verify that the mock was called correctly
            mock_client.images.remove.assert_called_with(image=image_name, force=False)
        finally:
            # Clean up the dependency override
            app.dependency_overrides.pop(get_podman_client)

    def test_by_id_success(self) -> None:
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
        image_id = (
            "sha256:a1801b843b1bfaf77c501e7a6d3f709401a1e0c83863037fa3aab063a7fdb9dc"
        )

        try:
            # Make the request to the endpoint
            response = client.delete(f"/api/images/?image_id={image_id}")

            # Verify the response - should be 204 No Content with no body
            assert response.status_code == 204
            assert response.content == b""  # Empty response body

            # Verify that the mock was called correctly
            mock_client.images.remove.assert_called_with(image=image_id, force=False)
        finally:
            # Clean up the dependency override
            app.dependency_overrides.pop(get_podman_client)

    def test_by_name_force(self) -> None:
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
            response = client.delete(f"/api/images/?image_name={image_name}&force=true")

            # Verify the response - should be 204 No Content with no body
            assert response.status_code == 204
            assert response.content == b""  # Empty response body

            # Verify that the mock was called correctly with force=True
            mock_client.images.remove.assert_called_with(image=image_name, force=True)
        finally:
            # Clean up the dependency override
            app.dependency_overrides.pop(get_podman_client)

    def test_by_id_force(self) -> None:
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
        image_id = (
            "sha256:a1801b843b1bfaf77c501e7a6d3f709401a1e0c83863037fa3aab063a7fdb9dc"
        )

        try:
            # Make the request to the endpoint with force=true
            response = client.delete(f"/api/images/?image_id={image_id}&force=true")

            # Verify the response - should be 204 No Content with no body
            assert response.status_code == 204
            assert response.content == b""  # Empty response body

            # Verify that the mock was called correctly with force=True
            mock_client.images.remove.assert_called_with(image=image_id, force=True)
        finally:
            # Clean up the dependency override
            app.dependency_overrides.pop(get_podman_client)

    def test_by_name_not_found(self) -> None:
        # Create a mock for the Podman client
        mock_client = MagicMock()
        mock_client.images.remove.side_effect = ImageNotFound("Image not found")

        # Override the dependency to use our mock
        app.dependency_overrides[get_podman_client] = lambda: mock_client

        # Nonexistent image name
        image_name = "nonexistent:latest"

        try:
            # Make the request to the endpoint
            response = client.delete(f"/api/images?image_name={image_name}")

            # Verify the response
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

            # Verify that the mock was called correctly
            mock_client.images.remove.assert_called_with(image=image_name, force=False)
        finally:
            # Clean up the dependency override
            app.dependency_overrides.pop(get_podman_client)

    def test_by_id_not_found(self) -> None:
        # Create a mock for the Podman client
        mock_client = MagicMock()
        mock_client.images.remove.side_effect = ImageNotFound("Image not found")

        # Override the dependency to use our mock
        app.dependency_overrides[get_podman_client] = lambda: mock_client

        # Nonexistent image name
        image_id = (
            "sha256:a1831b843b1bfaf77c521e7a6d3f709401a1e0c83863034fa3aab063a7fdb9ef"
        )

        try:
            # Make the request to the endpoint
            response = client.delete(f"/api/images?image_id={image_id}")

            # Verify the response
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

            # Verify that the mock was called correctly
            mock_client.images.remove.assert_called_with(image=image_id, force=False)
        finally:
            # Clean up the dependency override
            app.dependency_overrides.pop(get_podman_client)

    def test_by_name_in_use(self) -> None:
        mock_client = MagicMock()
        response_ = Response()
        response_.status_code = 409
        explanation = "image used by d384ed93e53fdfb5a41f4b72a21fcfae5526914512950eb76307d9f16418e00e: image is in use by a container: consider listing external containers and force-removing image"
        error = APIError(
            "image is in use by a container",
            response=response_,
            explanation=explanation,
        )
        mock_client.images.remove.side_effect = error

        app.dependency_overrides[get_podman_client] = lambda: mock_client

        image_name = "nginx:latest"

        try:
            # Make the request to the endpoint
            response = client.delete(f"/api/images?image_name={image_name}")

            # Verify the response
            assert response.status_code == 409
            assert "image used by" in response.json()["detail"]

            # Verify that the mock was called correctly
            mock_client.images.remove.assert_called_with(image=image_name, force=False)
        finally:
            # Clean up the dependency override
            app.dependency_overrides.pop(get_podman_client)

    def test_by_id_in_use(self) -> None:
        mock_client = MagicMock()
        response_ = Response()
        response_.status_code = 409
        explanation = "image used by d384ed93e53fdfb5a41f4b72a21fcfae5526914512950eb76307d9f16418e00e: image is in use by a container: consider listing external containers and force-removing image"
        error = APIError(
            "image is in use by a container",
            response=response_,
            explanation=explanation,
        )
        mock_client.images.remove.side_effect = error

        app.dependency_overrides[get_podman_client] = lambda: mock_client

        image_id = (
            "sha256:a1801b843b1bfaf77c501e7a6d3f709401a1e0c83863037fa3aab063a7fdb9dc"
        )

        try:
            # Make the request to the endpoint
            response = client.delete(f"/api/images?image_id={image_id}")

            # Verify the response
            assert response.status_code == 409
            assert "image used by" in response.json()["detail"]

            # Verify that the mock was called correctly
            mock_client.images.remove.assert_called_with(image=image_id, force=False)
        finally:
            # Clean up the dependency override
            app.dependency_overrides.pop(get_podman_client)

    def test_by_name_api_error(self) -> None:
        # Create a mock for the Podman client
        mock_client = MagicMock()
        mock_client.images.remove.side_effect = Exception("Something went wrong")

        # Override the dependency to use our mock
        app.dependency_overrides[get_podman_client] = lambda: mock_client

        # Image name that will cause an API error
        image_name = "nginx:latest"

        try:
            # Make the request to the endpoint
            response = client.delete(f"/api/images?image_name={image_name}")

            # Verify the response
            assert response.status_code == 500
            assert response.json()["detail"] == "Unexpected error"

            # Verify that the mock was called correctly
            mock_client.images.remove.assert_called_with(image=image_name, force=False)
        finally:
            # Clean up the dependency override
            app.dependency_overrides.pop(get_podman_client)

    def test_by_id_api_error(self) -> None:
        # Create a mock for the Podman client
        mock_client = MagicMock()
        mock_client.images.remove.side_effect = Exception("Something went wrong")

        # Override the dependency to use our mock
        app.dependency_overrides[get_podman_client] = lambda: mock_client

        # Image name that will cause an API error
        image_id = (
            "sha256:a1801b843b1bfaf77c501e7a6d3f709401a1e0c83863037fa3aab063a7fdb9dc"
        )

        try:
            # Make the request to the endpoint
            response = client.delete(f"/api/images?image_id={image_id}")

            # Verify the response
            assert response.status_code == 500
            assert response.json()["detail"] == "Unexpected error"

            # Verify that the mock was called correctly
            mock_client.images.remove.assert_called_with(image=image_id, force=False)
        finally:
            # Clean up the dependency override
            app.dependency_overrides.pop(get_podman_client)
