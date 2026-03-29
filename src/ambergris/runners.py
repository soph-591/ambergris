import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Iterable, Optional, Tuple

from docker.models.containers import Container
from docker.types import Mount
from docker.errors import NotFound

from .image import _cli, _resolve_image

logger = logging.getLogger(__name__)


@contextmanager
def open_container(
    image: Path | str, *mounts: Mount, **kwargs: Any
) -> Iterator[Container]:
    """Provides a managed Docker container context. Within the context of `ambergris`,
    the intent is to use it to pass commands in using `exec_command`. For example:

    ```
    # note: bindmounts are optional
    bindmounts = make_bindmounts(("/home/you/in/", "/container/in"))
    with ambergris.open_container("my-image:tag", mounts=bindmounts) as con:
        output = ambergris.exec_command(con, "/bin/bash -c 'find . -name *.txt'")
    ```

    The container is initialised using a non-terminating process ('tail -f /dev/null')
    to keep it alive for the duration of the context block. The container
    is automatically stopped and removed upon exit.

    Args:
        image: Name of the Docker image or Path to a .tar archive.
        mounts: Optional list of Docker Mount objects.
        **kwargs: Extra arguments passed to `client.containers.create`.

    Yields:
        docker.models.containers.Container: The initialized, running container.
    """
    container, _ = _init_container(
        image, command=["tail", "-f", "/dev/null"], mounts=mounts, **kwargs
    )
    container.start()
    try:
        yield container
    finally:
        _cleanup(container)


def _init_container(
    image: str | Path,
    command: Optional[str | list[str]] = None,
    *mounts: Mount,
    **kwargs: Any,
) -> Tuple[Container, Iterable]:
    cli = _cli()
    loaded_image = _resolve_image(image)
    kwargs.update(
        {
            "image": loaded_image.id,
            "detach": True,
            "auto_remove": False,
            "command": command,
            "mounts": mounts,
        }
    )
    container = cli.containers.create(**kwargs)
    stream = container.attach(
        stdout=True, stderr=True, stream=True, logs=True, demux=True
    )
    return container, stream


def _cleanup(container: Container) -> None:
    try:
        container.stop()
        container.remove()
    except NotFound:
        pass
    except Exception as e:
        logger.debug(f"Cleanup failed for {container.short_id}: {e}")


def exec_command(container: Container, command: str | list[str]) -> list[str]:
    """Executes a command inside an existing, running container. Within the context
    of `ambergris`, the intent is to use it inside the `open_container` context manager.
    For example:

    ```
    # note: bindmounts are optional
    bindmounts = make_bindmounts(("/home/you/in/", "/container/in"))
    with ambergris.open_container("my-image:tag", mounts=bindmounts) as con:
        output = ambergris.exec_command(con, "/bin/bash -c 'find . -name *.txt'")
    ```

    Args:
        container: A running Docker container instance.
        command: The command to execute (string or list of strings).

    Returns:
        list[str]: Decoded stdout and stderr lines from the execution.
    """
    _, stream = container.exec_run(cmd=command, stream=True, demux=True)
    result = _process_stream(stream)
    return result


def _process_stream(
    stream: Iterable[Tuple[Optional[bytes], Optional[bytes]]],
) -> list[str]:
    output = []
    for stdout, stderr in stream:
        if stdout:
            msg = stdout.decode().strip()
            output.append(msg)
            logger.info(msg)
        if stderr:
            msg = stderr.decode().strip()
            logger.warning(msg)
    return output


def run_container(
    image: Path | str,
    command: Optional[str | list[str]] = None,
    *mounts: Mount,
    **kwargs: Any,
) -> Tuple[list[str], int]:
    """Runs a command inside a Docker container and returns the results.

    This function initializes a container, captures the output
    stream, and ensures the container is cleaned up (stopped and removed)
    regardless of whether the command succeeds.

    Args:
        image: The name of the Docker image or a Path to a .tar archive.
        command: The command to run inside the container.
        mounts: A list of docker.types.Mount objects for data persistence.
        **kwargs: Additional arguments passed to the Docker containers.create call.

    Returns:
        A tuple containing:
            - A list of strings representing the decoded stdout/stderr lines.
            - An integer representing the container's exit status code.
    """
    container, stream = _init_container(image, command, *mounts, **kwargs)
    container.start()
    try:
        output = _process_stream(stream)
        exit_code = container.wait().get("StatusCode", -1)
        return output, exit_code
    finally:
        _cleanup(container)
