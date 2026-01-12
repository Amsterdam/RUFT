"""Tests for configuration loading."""

import tempfile
from pathlib import Path

import pytest

from ruft.config import RuftConfig, get_default_checks, load_config


def test_get_default_checks():
    """Test default check configuration."""
    checks = get_default_checks()

    assert "ruff_lint" in checks
    assert "ruff_format" in checks
    assert "mypy" in checks
    assert "pytest" in checks

    # Ruff checks should be enabled by default
    assert checks["ruff_lint"].enabled is True
    assert checks["ruff_format"].enabled is True

    # Optional checks should be disabled by default
    assert checks["mypy"].enabled is False
    assert checks["pytest"].enabled is False


def test_load_config_defaults():
    """Test loading config with no config file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to empty directory
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            config = load_config()

            assert isinstance(config, RuftConfig)
            assert config.settings.max_iterations == 3
            assert config.settings.auto_commit_fixes is True
            assert len(config.checks) > 0
        finally:
            os.chdir(old_cwd)


def test_load_yaml_config():
    """Test loading config from YAML file."""
    yaml_content = """
version: 1

settings:
  max_iterations: 5
  auto_commit_fixes: false

checks:
  ruff_lint:
    enabled: true
  mypy:
    enabled: true
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "ruft.yaml"
        config_path.write_text(yaml_content)

        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            config = load_config()

            assert config.settings.max_iterations == 5
            assert config.settings.auto_commit_fixes is False
            assert config.checks["ruff_lint"].enabled is True
            assert config.checks["mypy"].enabled is True
        finally:
            os.chdir(old_cwd)
