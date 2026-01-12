"""Virtual environment management for RUFT."""

import os
import subprocess
import sys
from pathlib import Path

from ruft.output.terminal import Colors, supports_color


def ensure_venv(project_root: Path) -> str:
    """Create or reuse a local venv for tools and return its python path.

    Creates a .ruft_venv directory in the project root with required tools.
    Falls back to system Python if venv creation fails.
    """
    cyan = Colors.CYAN if supports_color() else ""
    yellow = Colors.YELLOW if supports_color() else ""
    reset = Colors.RESET if supports_color() else ""

    venv_dir = project_root / ".ruft_venv"

    # Determine python executable path based on OS
    if os.name == "nt":
        py_path = venv_dir / "Scripts" / "python.exe"
    else:
        py_path = venv_dir / "bin" / "python"

    # Create venv if it doesn't exist
    if not py_path.exists():
        print(f"{cyan}[>] Creating RUFT virtual environment...{reset}")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                capture_output=True,
                text=True,
                cwd=project_root,
                check=False,
            )
            if result.returncode != 0:
                print(f"{yellow}[!] Failed to create venv, using system interpreter{reset}")
                return sys.executable
        except Exception as e:
            print(f"{yellow}[!] Venv creation error: {e}{reset}")
            return sys.executable

    # Install/upgrade pip and required tools
    print(f"{cyan}[>] Ensuring RUFT dependencies are installed...{reset}")

    # Install ruff (required)
    _install_package(str(py_path), "ruff", project_root)

    # Verify ruff works
    if not _verify_tool(str(py_path), "ruff"):
        print(f"{yellow}[!] Ruff not working, using system interpreter{reset}")
        return sys.executable

    # Optionally install mypy and pytest if available in requirements
    requirements_dev = project_root / "requirements_dev.txt"
    if requirements_dev.exists():
        _install_requirements(str(py_path), requirements_dev, project_root)

    return str(py_path)


def _install_package(python_path: str, package: str, cwd: Path) -> bool:
    """Install a package using pip."""
    try:
        result = subprocess.run(
            [python_path, "-m", "pip", "install", "--quiet", package],
            capture_output=True,
            text=True,
            cwd=cwd,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def _install_requirements(python_path: str, requirements_file: Path, cwd: Path) -> bool:
    """Install packages from requirements file."""
    try:
        result = subprocess.run(
            [python_path, "-m", "pip", "install", "--quiet", "-r", str(requirements_file)],
            capture_output=True,
            text=True,
            cwd=cwd,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def _verify_tool(python_path: str, tool: str) -> bool:
    """Verify a tool is installed and working."""
    try:
        result = subprocess.run(
            [python_path, "-m", tool, "--version"],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False
