import pytest
import pytest_mock
import docker.errors
import ambergris.runners


def test_init_container_configures_correctly(mocker: pytest_mock.MockerFixture):
    mock_dockerclient = mocker.MagicMock()

    mock_cli = mocker.patch("ambergris.runners._cli")
    mock_cli.return_value = mock_dockerclient

    mock_image = mocker.MagicMock(id="sha256:target-image")
    mock_resolveimage = mocker.patch("ambergris.runners._resolve_image")
    mock_resolveimage.return_value = mock_image

    ambergris.runners._init_container("target-image", command=["/bin/bash", "-c", "ls"])

    mock_dockerclient.containers.create.assert_called_once()
    _, kwargs = mock_dockerclient.containers.create.call_args
    assert kwargs["image"] == "sha256:target-image"
    assert kwargs["detach"] is True
    assert kwargs["auto_remove"] is False


def test_cleanup_stops_and_removes(mock_container):
    ambergris.runners._cleanup(mock_container)
    mock_container.stop.assert_called_once()
    mock_container.remove.assert_called_once()


def test_cleanup_ignores_not_found(mock_container):
    mock_container.stop.side_effect = docker.errors.NotFound("Gone")
    ambergris.runners._cleanup(mock_container)
    assert mock_container.stop.called


def test_open_container(mocker: pytest_mock.MockerFixture, mock_container):
    mock_initcontainer = mocker.patch("ambergris.runners._init_container")
    mock_initcontainer.return_value = (mock_container, iter([]))

    mock_cleanup = mocker.patch("ambergris.runners._cleanup")

    with ambergris.runners.open_container("image") as container:
        assert container == mock_container
        mock_container.start.assert_called_once()
        mock_cleanup.assert_not_called()

    mock_cleanup.assert_called_once_with(mock_container)


def test_process_stream(caplog):
    mock_stream = [(b"hello world\n", None), (None, b"some warning\n")]

    with caplog.at_level("INFO"):
        output = ambergris.runners._process_stream(mock_stream)
        assert "hello world" in output
        assert "hello world" in caplog.text
        assert "some warning" in caplog.text


def test_exec_command(mock_container):
    mock_stream = iter([(b"exec result", None)])
    mock_container.exec_run.return_value = (0, mock_stream)

    result = ambergris.runners.exec_command(mock_container, ["ls"])

    assert result == ["exec result"]
    mock_container.exec_run.assert_called_with(cmd=["ls"], stream=True, demux=True)


def test_run_container(mocker: pytest_mock.MockerFixture, mock_container):
    mock_container.wait.return_value = {"StatusCode": 42}

    mock_initcontainer = mocker.patch("ambergris.runners._init_container")
    mock_stream = iter([(b"hello world\n", None)])
    mock_initcontainer.return_value = (mock_container, mock_stream)

    mocker.patch("ambergris.runners._cleanup")

    output, exit_code = ambergris.runners.run_container("image", ["ls"])

    assert output == ["hello world"]
    assert exit_code == 42
