import pytest
import pytest_mock
import docker.errors
import docker.models.images

import ambergris.image


def test_cli_singleton(mocker: pytest_mock.MockerFixture):
    mock_fromenv = mocker.patch("docker.from_env")
    mock_fromenv.return_value = mocker.MagicMock
    client_a = ambergris.image._cli()
    client_b = ambergris.image._cli()

    mock_fromenv.assert_called_once()
    assert client_a is client_b


def test_resolve_image_calls_images_get(mocker):
    mock_image = mocker.MagicMock()
    mock_dockerclient = mocker.MagicMock()
    mock_dockerclient.images.get.return_value = mock_image
    mock_cli = mocker.patch("ambergris.image._cli")
    mock_cli.return_value = mock_dockerclient

    result = ambergris.image._resolve_image("alpine:3.18")
    mock_dockerclient.images.get.assert_called_with("alpine:3.18")
    assert result == mock_image


def test_resolve_image_calls_load_image_when_images_get_fails(
    mocker: pytest_mock.MockerFixture,
):
    mock_image = mocker.MagicMock(spec=docker.models.images.Image)

    mock_dockerclient = mocker.MagicMock()
    mock_dockerclient.images.get.side_effect = docker.errors.ImageNotFound("Not found")
    mock_dockerclient.images.load.return_value = [mock_image]

    mock_cli = mocker.patch("ambergris.image._cli")
    mock_cli.return_value = mock_dockerclient

    mock_loadimage = mocker.patch("ambergris.image._load_image")
    mock_loadimage.return_value = mock_image

    result = ambergris.image._resolve_image("image.tar")

    mock_loadimage.assert_called_once_with("image.tar")
    assert result == mock_image


def test_load_image(mocker):
    mock_image = mocker.MagicMock(spec=docker.models.images.Image)
    mock_dockerclient = mocker.MagicMock()
    mock_dockerclient.images.load.return_value = [mock_image]

    mock_file_handle = mocker.mock_open()
    mocker.patch("builtins.open", mock_file_handle)

    mocker.patch("ambergris.image._cli", return_value=mock_dockerclient)

    result = ambergris.image._load_image("image.tar")

    assert result == mock_image
    mock_file_handle.assert_called_once_with("image.tar", "rb")
    entered_file_handle = mock_file_handle()
    mock_dockerclient.images.load.assert_called_once_with(entered_file_handle)


def test_load_image_empty_tar_raises_error(mocker: pytest_mock.MockerFixture):
    mock_dockerclient = mocker.MagicMock()
    mock_dockerclient.images.load.return_value = []

    mock_cli = mocker.patch("ambergris.image._cli")
    mock_cli.return_value = mock_dockerclient

    mock_file_handle = mocker.mock_open()
    mocker.patch("builtins.open", mock_file_handle(read_data=b""))

    with pytest.raises(docker.errors.ImageLoadError):
        ambergris.image._load_image("empty.tar")


def test_load_image_warning_on_multiple(mocker: pytest_mock.MockerFixture, recwarn):
    mock_images = [
        mocker.MagicMock(short_id="sha256:12345"),
        mocker.MagicMock(short_id="sha256:34567"),
    ]

    mock_dockerclient = mocker.MagicMock()
    mock_dockerclient.images.load.return_value = mock_images

    mock_cli = mocker.patch("ambergris.image._cli")
    mock_cli.return_value = mock_dockerclient

    mocker.patch("builtins.open", mocker.mock_open(read_data=b"multi"))

    result = ambergris.image._load_image("multi.tar")

    assert result == mock_images[0]
    assert len(recwarn) == 1
