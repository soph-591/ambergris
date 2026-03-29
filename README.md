# ambergris

[![CI Status](https://github.com/soph-591/ambergris/actions/workflows/ci.yml/badge.svg)](https://github.com/soph-591/ambergris/actions) [![PyPI Version](https://img.shields.io/pypi/v/ambergris.svg)](https://pypi.org/project/ambergris/) [![Python Versions](https://img.shields.io/pypi/pyversions/ambergris.svg)](https://pypi.org/project/ambergris/) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`ambergris` is a lightweight Python utility that simplifies the process of running commands in Docker containers. 

Let's say you have a Docker image containing a simple Python tool that reads in .xlsx files, and stores the processed results as a CSV. A typical example of how `ambergris` can help here is as follows. The example covers path translation, creating bind-type mounts, and executing a command in a container:

```python
import ambergris
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

@ambergris.make_io_relative_to_container
def my_bash_command(in_data, out_file, mounts):
    return f"/bin/bash -c 'python3 my_tool.py --in {in_data} --out {out_file}.csv'"
    
if __name__ == "__main__":
    # makes mount mappings: (host-path -> container-path)
    mounts = ambergris.make_bindmounts(
        ("/home/you/inputs/", "/container/in/"),
        ("/home/you/outputs/", "/container/out/")
    )
    cmd = my_bash_command("/home/you/inputs/data.xlsx", out_file="/home/you/outputs/data.csv", mounts=mounts)
    output, exit_code = ambergris.run_command("my-image:0.1", cmd, mounts)
    with open("/home/you/outputs/data.csv", "r") as f:
        print(f.readlines())
```

`ambergris` automatically closes and cleans up containers when your image has stopped running. It also supports running from images that are stored remotely in a Docker registry, locally in the Docker daemon, or locally from a `tar(.gz)` archived image. For example:

```python
import ambergris

ambergris.run_command(image="/home/you/my_python_image.tar.gz", cmd=["python3", "my_program.py", "-h"])
```

## Installation

```bash
pip install ambergris
```

## Quick Start
### 1. Logging Setup

Ambergris uses the standard logging module. To see container output and lifecycle warnings, set your log level to INFO:

```python
import logging
import ambergris

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
```

### 2. Running Tasks

Use run_container for "one-and-done" scripts. This handles the full lifecycle: loading the image, running the command, and cleaning up the container.

```python
# Create mounts (Host Path, Container Path)
mounts = ambergris.make_bindmounts(
    ("~/input_data", "/in"),
    ("./results", "/out")
)

# Run a command (supports strings or lists)
command = ["/bin/sh", "-c", "ls -l /in"]

output, exit_code = ambergris.run_container("alpine:latest", command, mounts=mounts)

print(f"Exited with code: {exit_code}")
for line in output:
    print(line)
```

### 3. Persistent Sessions

Use `open_container` to run multiple commands within the same environment without the overhead of restarting the container.

```python
with ambergris.open_container("alpine:latest", mounts) as container:
    # Execute multiple commands in the same instance
    ambergris.exec_command(container, "touch /tmp/session.log")
    ambergris.exec_command(container, 'sh -c "echo 'hello' > /tmp/session.log"')
    
    results = ambergris.exec_command(container, "cat /tmp/session.log")
    print(results)  # ['hello']

# Container is automatically stopped and removed after the 'with' block
```

### 4. Working with Local Tar Archives

If you have an image saved as a tarball (raw .tar or gzipped .tar.gz), simply pass the path instead of an image name. `ambergris` will automatically load it into the Docker daemon.

```python
output, exit_code = ambergris.run_container("./my_custom_image.tar.gz", command=["whoami"])
```

### 5. Automatic Path Mapping (Decorator)

The `@make_io_relative_to_container` decorator is useful when your Python functions take host `Path` objects but need to reference where those files live inside the container.

```python
from pathlib import Path

@ag.make_io_relative_to_container
def process_data(input_file: Path, mounts: list):
    print(f"Path inside container: {input_file}")
```

## Development

If you are contributing to `ambergris`, install the dev dependencies:

```bash
pip install -e ".[dev]"
pytest
```