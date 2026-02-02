# RUFT - Ruff-based Universal Fixer Tool

A transparent, configurable quality check and auto-fix workflow for Python projects.

<details>
<summary><b>See it in action</b> (click to expand)</summary>

**Before** - Code with issues:
```python
import os,sys
from typing import *
def calculate_thing(x,y,z):
  result=x+y*z
  unused_var = 42
  return result
class myClass:
    def __init__(self,value):self.value=value
```

**What RUFT detects:**
- `ruff check`: Unused imports (`os`, `sys`), wildcard import, unused variable, naming convention (`myClass` → `MyClass`)
- `ruff format`: Spacing, indentation, line length
- `mypy`: Missing type annotations

**After** - Auto-fixed:
```python
def calculate_thing(x: float, y: float, z: float) -> float:
    result = x + y * z
    return result


class MyClass:
    def __init__(self, value: int) -> None:
        self.value = value
```

</details>

## Features

- **Iterative auto-fix**: Runs checks in a loop until no more fixes are possible
- **Pluggable checks**: Enable/disable Ruff lint, Ruff format, MyPy, pytest
- **Custom checks**: Add your own shell commands as quality checks
- **Cross-platform**: Works on Windows, Linux, and macOS
- **Git integration**: Auto-commit fixes, optional auto-push
- **Beautiful output**: Colored terminal output with progress indicators

## Installation

```bash
# Basic installation (ruff only)
pip install git+https://github.com/Amsterdam/RUFT.git

# With all optional checks (mypy, pytest)
pip install "git+https://github.com/Amsterdam/RUFT.git#egg=ruft[all]"
```

## Quick Start

```bash
# Initialize config files in your project (optional)
ruft --init

# Run all enabled checks
ruft

# Dry run (show what would happen without making changes)
ruft --dry-run

# Run specific checks only
ruft --check ruff_lint ruff_format

# Run checks but don't push
ruft --no-push
```

## How It Works

RUFT replaces pre-commit hooks with a transparent workflow:

1. Detects uncommitted changes and optionally commits them
2. Runs quality checks in iterations (up to 3 by default)
3. Auto-fixes what it can (Ruff linting and formatting)
4. Re-commits any fixes automatically
5. Repeats until no more auto-fixes are possible
6. Shows final status report
7. Optionally pushes if all checks pass

## Configuration

Create `ruft.yaml` in your project root:

```yaml
version: 1

settings:
  max_iterations: 3          # Max auto-fix iterations
  auto_commit_fixes: true    # Commit auto-fixes automatically
  commit_message_prefix: "Auto-fix:"

git:
  auto_push: false           # Push after all checks pass
  require_clean_start: false # Require no uncommitted changes

checks:
  ruff_lint:
    enabled: true
    config_file: ".ruff.toml"

  ruff_format:
    enabled: true
    config_file: ".ruff.toml"

  mypy:
    enabled: false           # Disabled by default (optional dependency)
    config_file: "pyproject.toml"

  pytest:
    enabled: false           # Disabled by default (optional dependency)
    test_dir: "tests"
    extra_args: ["-v"]
```

### Configuration Priority

1. CLI arguments (highest priority)
2. `ruft.yaml` in current directory
3. `pyproject.toml` `[tool.ruft]` section
4. Built-in defaults (lowest priority)

## Bundled Ruff Configuration

RUFT includes a well-tuned `.ruff.toml` as a starting point:

```bash
ruft --init  # Creates .ruff.toml and ruft.yaml
```

The bundled configuration includes:
- 150 character line length
- Comprehensive lint rules (pyflakes, pycodestyle, isort, pep8 naming, etc.)
- Sensible ignores for common conflicts
- Per-file ignores for tests and scripts

## Custom Checks

Add custom commands in `ruft.yaml`:

```yaml
checks:
  custom:
    - name: "Security Scan"
      enabled: true
      command: "bandit -r src/"
      can_auto_fix: false

    - name: "Dependency Check"
      enabled: true
      command: "pip-audit"
      can_auto_fix: false
```

## GitHub Actions

Enforce code quality in CI/CD by running the same checks RUFT uses locally.

[![Code Quality](https://github.com/Amsterdam/RUFT/actions/workflows/ruft.yml/badge.svg)](https://github.com/Amsterdam/RUFT/actions/workflows/ruft.yml)

### Recommended Approach

Run the raw tools directly in CI rather than RUFT itself. This ensures:
- **Full error output visible** - Platform-specific issues (Ubuntu CI vs Windows local) are shown in detail
- **No hidden failures** - Each check's errors are clearly visible in the pipeline logs
- **Developers use RUFT locally** - To auto-fix issues caught by CI

### Example Workflow

Create `.github/workflows/ci.yml` in your repository:

```yaml
name: Code Quality

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install ruff mypy pytest
          pip install -r requirements.txt  # if you have one

      - name: Ruff lint
        run: ruff check .

      - name: Ruff format
        run: ruff format --check .

      - name: MyPy
        run: mypy .

      - name: Tests
        run: pytest tests/
```

### Workflow Design

Each check runs as a separate step so that:
1. Errors show full output in the GitHub Actions log
2. You can see exactly which check failed and why
3. Platform-specific issues (e.g., mypy finding something on Linux but not Windows) are visible

When CI fails, developers run `ruft` locally to auto-fix what can be fixed, then address remaining issues shown in the CI output.

### Blocking Merges on Failure

To require passing checks before merging:

1. Go to your repository **Settings** → **Branches**
2. Add or edit a branch protection rule for `main`
3. Enable **"Require status checks to pass before merging"**
4. Select **"quality-check"** from the list

## CLI Reference

```
usage: ruft [-h] [--dry-run] [--no-push] [--init] [--check [CHECK ...]]
            [-c CONFIG] [-v] [--version]

RUFT - Ruff-based Universal Fixer Tool

options:
  -h, --help            Show this help message and exit
  --dry-run             Show what would happen without making changes
  --no-push             Run checks and commit fixes, but don't push
  --init                Initialize RUFT config files in current directory
  --check [CHECK ...]   Run specific checks only (e.g., --check ruff_lint)
  -c, --config CONFIG   Path to ruft.yaml configuration file
  -v, --verbose         Enable verbose output
  --version             Show program version and exit
```

## Requirements

- Python 3.10+
- Git (for version control operations)
- Ruff (automatically installed)

Optional:
- MyPy (for type checking): `pip install ruft[mypy]`
- pytest (for testing): `pip install ruft[pytest]`

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
