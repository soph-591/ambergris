import pytest
import pytest_mock
from pathlib import Path
import ambergris.image

import docker.types


@pytest.fixture(autouse=True)
def reset_docker_client():
    with ambergris.image._CLIENT_LOCK:
        ambergris.image._CLIENT = None
    yield


@pytest.fixture
def mock_container(mocker: pytest_mock.MockerFixture):
    container = mocker.MagicMock()
    container.short_id = "abc12345"
    container.wait.return_value = {"StatusCode": 0}
    return container


@pytest.fixture
def test_bindmounts(tmp_path) -> list[docker.types.Mount]:
    test_mount_a = docker.types.Mount(
        source=str(tmp_path / "host" / "test" / "in"),
        target="/container/test/in",
        type="bind",
    )
    test_mount_b = docker.types.Mount(
        source=str(tmp_path / "host" / "test" / "out"),
        target="/container/test/out",
        type="bind",
    )
    return [test_mount_a, test_mount_b]
