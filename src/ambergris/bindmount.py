import warnings
from pathlib import Path
from functools import wraps
from typing import Any, Callable, Tuple, TypeVar, cast
from docker.types import Mount

F = TypeVar("F", bound=Callable[..., Any])


def make_io_relative_to_container(func: F) -> F:
    """Decorator to translate host Path arguments to container-relative Paths.
    The typical use-case for this decorator is when you write a function that
    compiles a command to run in a container, and you need to translate the host filepaths
    into filepaths relative to the container.

    For example:

    ```
    import ambergris

    # note: you must supply a mounts argument to your decorated function
    @ambergris.make_io_relative_to_container
    def my_bash_command(in_data: Path, out_file: Path, mounts: list[Mount]):
        return f"/bin/bash -c 'python3 my_tool.py --in {in_data} --out {out_file}.csv'"

    if __name__ == "__main__":
        mounts = ambergris.make_bindmounts(
            ("/home/you/inputs/", "/container/in/"),
            ("/home/you/outputs/", "/container/out/")
        )
        # note that mounts MUST be submitted as a keyword when executing your command-builder, so ambergris recognises them as mounts
        cmd = my_bash_command("/home/you/inputs/data.xlsx", out_file="/home/you/outputs/data.csv", mounts=mounts)
        ambergris.run_command("my-image:0.1", cmd, mounts)
        with open("/home/you/outputs/data.csv", "r") as f:
            print(f.readlines())
    ```

    When the decorated function is called, any `pathlib.Path` passed as an
    argument or keyword argument is checked against the provided `mounts`.
    If a match is found, the path is rewritten to its path inside the container.

    Note:
        The decorated function MUST accept a `mounts` keyword argument
        containing a list of `docker.types.Mount` objects.

    Args:
        func: The function to be decorated.

    Returns:
        Callable: The wrapped function with path translation logic.
    """

    @wraps(func)
    def wrapper(*args: Any, mounts: list[Mount], **kwargs: Any) -> Any:
        new_args = [
            get_container_path(arg, *mounts) if isinstance(arg, Path) else arg
            for arg in args
        ]
        new_kwargs = {
            k: (get_container_path(v, *mounts) if isinstance(v, Path) else v)
            for k, v in kwargs.items()
        }
        return func(*new_args, mounts=mounts, **new_kwargs)

    return cast(F, wrapper)


def get_container_path(file_path: Path, *mounts: Mount) -> Path:
    """Translates a host file path to its corresponding path inside a container.

    Iterates through the provided mounts to see if `file_path` resides within
    a host source directory. If so, it returns the path relative to the
    container target. A warning is raised if the file path cannot be resolved
    from any of the mount configurations - in this case, the unchanged file path
    is returned.

    Args:
        file_path: The absolute path on the host machine.
        *mounts: Variable number of Docker Mount objects to check against.

    Returns:
        Path: The translated container path if a match is found;
              otherwise, the original file_path.
    """
    file_path = file_path.resolve()
    for mount in mounts:
        host = Path(mount["Source"]).resolve()
        container = Path(mount["Target"])
        try:
            return container / file_path.relative_to(host)
        except ValueError:
            continue
    warnings.warn(f"{file_path} not found in bindmount config. Returning as-is...")
    return file_path


def make_bindmounts(*bindings: Tuple[str | Path, str | Path]) -> list[Mount]:
    """Creates a list of Docker bind mounts from multiple source/target pairs.
    This is a wrapper around `ambergris.make_bindmount` which allows you to create
    multiple bindmounts at once.

    Args:
        *bindings: Variable length argument of tuples, where each tuple
            contains (source_path, target_path).

    Returns:
        A list of initialized docker.types.Mount objects.
    """
    return [make_bindmount(*binding) for binding in bindings]


def make_bindmount(src: str | Path, dst: str | Path) -> Mount:
    """Creates a single Docker bind mount object.

    Handles path expansion (e.g., '~') and converts paths to absolute
    to ensure the Docker daemon can resolve them correctly.

    Args:
        src: The host directory or file to mount.
        dst: The destination path inside the container.

    Returns:
        A Mount object configured with the 'bind' type.
    """
    src_exp = Path(src).expanduser().absolute()
    dst_exp = Path(dst).expanduser().absolute()
    return Mount(source=str(src_exp), target=str(dst_exp), type="bind")
