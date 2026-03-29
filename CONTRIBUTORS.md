# Contributing to ambergris

## Code of Conduct

By participating in this project, you agree to maintain a professional and respectful environment for all contributors.

## How to Get Started

### Cloning and Forking Ambergris

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:

```bash
git clone https://github.com/soph-591/ambergris.git
```
### Set up your development environment

We use hatchling as the build backend. Install the package in editable mode with all development dependencies:

```
pip install -e ".[dev]"
```

## Development Standards

To keep the codebase clean and maintainable, we enforce the following standards:

### 1. Code Style

We use Black for code formatting. Before submitting a Pull Request, please run:

```bash
black src/ test/
```

### 2. Type Hinting

We use Mypy for static type checking:

```bash
mypy src/
```

### 3. Testing

No pull request will be merged without passing tests. We use Pytest.

Unit Tests: Ensure your changes don't break existing logic.

New Features: If you add a feature, you must add a corresponding test in the tests/ directory.

Run the suite with:

```bash
pytest
```

## Creating a Pull Request

Create a feature branch: `git checkout -b feature/your-new-feature`

Commit your changes: Use clear, descriptive commit messages.

Push to your fork: `git push origin feature/your-new-feature`

Open a Pull Request: Provide a clear description of what your changes do and why they are necessary.

#### Questions?

If you have questions or feedback about the codebase, or a specific feature request, please open an Issue on GitHub.