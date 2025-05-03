from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.dependencies import get_podman_client
from app.main import app

client = TestClient(app)


def test_info() -> None:
    info = {
        "host": {
            "arch": "arm64",
            "buildahVersion": "1.0.0",
            "cgroupControllers": ["cpu", "io", "memory", "pids"],
            "cgroupManager": "systemd",
            "cgroupVersion": "v2",
            "conmon": {
                "package": "conmon-1.0.0-generic",
                "path": "/usr/bin/conmon",
                "version": "conmon version 1.0.0, commit: abcdef",
            },
            "cpuUtilization": {
                "idlePercent": 98.0,
                "systemPercent": 1.0,
                "userPercent": 1.0,
            },
            "cpus": 4,
            "databaseBackend": "sqlite",
            "distribution": {
                "distribution": "genericlinux",
                "variant": "base",
                "version": "1.0",
            },
            "eventLogger": "journald",
            "freeLocks": 1024,
            "hostname": "example.local",
            "idMappings": {
                "gidmap": [
                    {"container_id": 0, "host_id": 1001, "size": 1},
                    {"container_id": 1, "host_id": 200000, "size": 1000000},
                ],
                "uidmap": [
                    {"container_id": 0, "host_id": 1001, "size": 1},
                    {"container_id": 1, "host_id": 200000, "size": 1000000},
                ],
            },
            "kernel": "5.10.0-generic",
            "linkmode": "dynamic",
            "logDriver": "journald",
            "memFree": 2147483648,
            "memTotal": 4294967296,
            "networkBackend": "netavark",
            "networkBackendInfo": {
                "backend": "netavark",
                "dns": {
                    "package": "aardvark-dns-1.0.0-generic",
                    "path": "/usr/libexec/podman/aardvark-dns",
                    "version": "aardvark-dns 1.0.0",
                },
                "package": "netavark-1.0.0-generic",
                "path": "/usr/libexec/podman/netavark",
                "version": "netavark 1.0.0",
            },
            "ociRuntime": {
                "name": "crun",
                "package": "crun-1.0.0-generic",
                "path": "/usr/bin/crun",
                "version": """crun version 1.0.0
commit: deadbeefcafebabe
rundir: /run/user/1001/crun
spec: 1.0.0
+SYSTEMD +SELINUX +SECCOMP""",
            },
            "os": "linux",
            "pasta": {
                "executable": "/usr/bin/pasta",
                "package": "passt-1.0.0-generic",
                "version": """pasta 1.0.0-generic
Copyright Example
GNU General Public License, version 2 or later

This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.""",
            },
            "remoteSocket": {"exists": True, "path": "tcp:127.0.0.1:9999"},
            "rootlessNetworkCmd": "pasta",
            "security": {
                "apparmorEnabled": False,
                "capabilities": "CAP_SYS_ADMIN,CAP_NET_ADMIN",
                "rootless": True,
                "seccompEnabled": True,
                "seccompProfilePath": "/usr/share/containers/seccomp.json",
                "selinuxEnabled": False,
            },
            "serviceIsRemote": False,
            "slirp4netns": {
                "executable": "/usr/bin/slirp4netns",
                "package": "slirp4netns-1.0.0-generic",
                "version": """slirp4netns version 1.0.0
commit: abc123
libslirp: 4.0.0
SLIRP_CONFIG_VERSION_MAX: 5
libseccomp: 2.5.0""",
            },
            "swapFree": 0,
            "swapTotal": 0,
            "uptime": "0h 10m 00.00s",
            "variant": "v1",
        },
        "plugins": {
            "authorization": None,
            "log": ["k8s-file", "none", "passthrough", "journald"],
            "network": ["bridge", "macvlan", "ipvlan"],
            "volume": ["local"],
        },
        "registries": {"search": ["example.io"]},
        "store": {
            "configFile": "/home/user/.config/containers/storage.conf",
            "containerStore": {"number": 0, "paused": 0, "running": 0, "stopped": 0},
            "graphDriverName": "overlay",
            "graphOptions": {},
            "graphRoot": "/home/user/.local/share/containers/storage",
            "graphRootAllocated": 50000000000,
            "graphRootUsed": 1234567890,
            "graphStatus": {
                "Backing Filesystem": "ext4",
                "Native Overlay Diff": "true",
                "Supports d_type": "true",
                "Supports shifting": "false",
                "Supports volatile": "true",
                "Using metacopy": "false",
            },
            "imageCopyTmpDir": "/tmp",
            "imageStore": {"number": 0},
            "runRoot": "/run/user/1001/containers",
            "transientStore": False,
            "volumePath": "/home/user/.local/share/containers/storage/volumes",
        },
        "version": {
            "APIVersion": "1.0.0",
            "BuildOrigin": "Example Project",
            "Built": 1700000000,
            "BuiltTime": "Mon Jan  1 00:00:00 2024",
            "GitCommit": "abcdef1234567890",
            "GoVersion": "go1.21.0",
            "Os": "linux",
            "OsArch": "linux/arm64",
            "Version": "1.0.0",
        },
    }

    mock_client = MagicMock()
    mock_client.info.return_value = info
    app.dependency_overrides[get_podman_client] = lambda: mock_client
    try:
        response = client.get("/api/info")
        assert response.status_code == 200
        assert response.json() == info
        mock_client.info.assert_called_once()
    finally:
        app.dependency_overrides.pop(get_podman_client)
