import threading
import warnings
from pathlib import Path
from typing import Optional
import docker
from docker.models.images import Image
from docker.errors import ImageNotFound, ImageLoadError

# client singleton
_CLIENT: Optional[docker.DockerClient] = None
_CLIENT_LOCK: threading.Lock = threading.Lock()


def _cli() -> docker.DockerClient:
    global _CLIENT
    if _CLIENT is None:
        with _CLIENT_LOCK:
            if _CLIENT is None:
                _CLIENT = docker.from_env()
    return _CLIENT


def _resolve_image(image: Path | str) -> Image:
    client = _cli()
    try:
        loaded_image = client.images.get(str(image))
    except ImageNotFound:
        loaded_image = _load_image(image)
    return loaded_image


def _load_image(image: Path | str) -> Image:
    client = _cli()
    with open(image, "rb") as f:
        loaded_images = client.images.load(f)
    if not loaded_images:
        raise ImageLoadError(f"Tar archive of {image} contained no loadable images")
    elif len(loaded_images) > 1:
        warnings.warn(f"Tar archive of {image} contained {len(loaded_images)} images. \
                       Defaulting to the first one found ({loaded_images[0].short_id})")
    return loaded_images[0]
