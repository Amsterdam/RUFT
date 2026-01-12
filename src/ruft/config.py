"""Configuration loading and management."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CheckConfig:
    """Configuration for a single check."""

    name: str = ""
    enabled: bool = True
    can_auto_fix: bool = False
    command: str | None = None
    config_file: str | None = None
    test_dir: str | None = None
    extra_args: list[str] = field(default_factory=list)


@dataclass
class GitConfig:
    """Git workflow configuration."""

    auto_push: bool = False
    require_clean_start: bool = False


@dataclass
class Settings:
    """Global settings."""

    max_iterations: int = 3
    auto_commit_fixes: bool = True
    commit_message_prefix: str = "Auto-fix:"


@dataclass
class RuftConfig:
    """Complete RUFT configuration."""

    version: int = 1
    settings: Settings = field(default_factory=Settings)
    git: GitConfig = field(default_factory=GitConfig)
    checks: dict[str, CheckConfig] = field(default_factory=dict)


def get_default_checks() -> dict[str, CheckConfig]:
    """Get default check configurations."""
    return {
        "ruff_lint": CheckConfig(
            name="Ruff Style Check",
            enabled=True,
            can_auto_fix=True,
            config_file=".ruff.toml",
        ),
        "ruff_format": CheckConfig(
            name="Ruff Formatter",
            enabled=True,
            can_auto_fix=True,
            config_file=".ruff.toml",
        ),
        "mypy": CheckConfig(
            name="MyPy Type Check",
            enabled=False,  # Disabled by default (optional dep)
            can_auto_fix=False,
            config_file="pyproject.toml",
        ),
        "pytest": CheckConfig(
            name="Tests",
            enabled=False,  # Disabled by default (optional dep)
            can_auto_fix=False,
            test_dir="tests",
        ),
    }


def _parse_check_config(check_data: dict[str, Any]) -> CheckConfig:
    """Parse a check configuration from dict."""
    return CheckConfig(
        name=check_data.get("name", ""),
        enabled=check_data.get("enabled", True),
        can_auto_fix=check_data.get("can_auto_fix", False),
        command=check_data.get("command"),
        config_file=check_data.get("config_file"),
        test_dir=check_data.get("test_dir"),
        extra_args=check_data.get("extra_args", []),
    )


def _load_yaml_config(config_path: Path) -> RuftConfig:
    """Load configuration from YAML file."""
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    config = RuftConfig()
    config.version = data.get("version", 1)

    # Parse settings
    if "settings" in data:
        settings_data = data["settings"]
        config.settings = Settings(
            max_iterations=settings_data.get("max_iterations", 3),
            auto_commit_fixes=settings_data.get("auto_commit_fixes", True),
            commit_message_prefix=settings_data.get("commit_message_prefix", "Auto-fix:"),
        )

    # Parse git config
    if "git" in data:
        git_data = data["git"]
        config.git = GitConfig(
            auto_push=git_data.get("auto_push", False),
            require_clean_start=git_data.get("require_clean_start", False),
        )

    # Start with defaults and override with config
    config.checks = get_default_checks()

    if "checks" in data:
        checks_data = data["checks"]
        for check_name, check_data in checks_data.items():
            if check_name == "custom":
                # Handle custom checks list
                if isinstance(check_data, list):
                    for i, custom in enumerate(check_data):
                        custom_name = f"custom_{i}"
                        config.checks[custom_name] = _parse_check_config(custom)
            elif isinstance(check_data, dict):
                if check_name in config.checks:
                    # Update existing check
                    existing = config.checks[check_name]
                    existing.enabled = check_data.get("enabled", existing.enabled)
                    existing.config_file = check_data.get("config_file", existing.config_file)
                    existing.extra_args = check_data.get("extra_args", existing.extra_args)
                    existing.test_dir = check_data.get("test_dir", existing.test_dir)
                else:
                    # New check
                    config.checks[check_name] = _parse_check_config(check_data)

    return config


def _load_pyproject_config(pyproject_path: Path) -> RuftConfig | None:
    """Try to load configuration from pyproject.toml [tool.ruft] section."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[import-not-found, no-redef]
        except ImportError:
            return None

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        if "tool" not in data or "ruft" not in data["tool"]:
            return None

        ruft_data = data["tool"]["ruft"]

        # Convert to yaml-like format and parse
        config = RuftConfig()
        config.checks = get_default_checks()

        if "settings" in ruft_data:
            settings = ruft_data["settings"]
            config.settings = Settings(
                max_iterations=settings.get("max_iterations", 3),
                auto_commit_fixes=settings.get("auto_commit_fixes", True),
                commit_message_prefix=settings.get("commit_message_prefix", "Auto-fix:"),
            )

        if "checks" in ruft_data:
            for check_name, check_data in ruft_data["checks"].items():
                if check_name in config.checks and isinstance(check_data, dict):
                    existing = config.checks[check_name]
                    existing.enabled = check_data.get("enabled", existing.enabled)

        return config
    except Exception:
        return None


def load_config(config_path: Path | None = None) -> RuftConfig:
    """Load configuration from file or use defaults.

    Priority:
    1. Explicit config_path argument
    2. ruft.yaml in current directory
    3. pyproject.toml [tool.ruft] section
    4. Built-in defaults
    """
    cwd = Path.cwd()

    # Try explicit path first
    if config_path and config_path.exists():
        return _load_yaml_config(config_path)

    # Try ruft.yaml
    yaml_path = cwd / "ruft.yaml"
    if yaml_path.exists():
        return _load_yaml_config(yaml_path)

    # Try pyproject.toml
    pyproject_path = cwd / "pyproject.toml"
    if pyproject_path.exists():
        config = _load_pyproject_config(pyproject_path)
        if config:
            return config

    # Return defaults
    config = RuftConfig()
    config.checks = get_default_checks()
    return config


def create_default_config(project_root: Path) -> int:
    """Create default configuration files in the project.

    Returns 0 on success, 1 on failure.
    """
    from ruft.output.terminal import Colors, supports_color

    green = Colors.GREEN if supports_color() else ""
    yellow = Colors.YELLOW if supports_color() else ""
    reset = Colors.RESET if supports_color() else ""

    # Create ruft.yaml
    ruft_yaml = project_root / "ruft.yaml"
    if not ruft_yaml.exists():
        ruft_yaml_content = """# RUFT Configuration
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
    enabled: false           # Enable if you have mypy installed
    config_file: "pyproject.toml"

  pytest:
    enabled: false           # Enable if you have pytest installed
    test_dir: "tests"
    extra_args: ["-v"]

  # Example custom checks:
  # custom:
  #   - name: "Security Scan"
  #     enabled: false
  #     command: "bandit -r src/"
  #     can_auto_fix: false
"""
        with open(ruft_yaml, "w", encoding="utf-8") as f:
            f.write(ruft_yaml_content)
        print(f"{green}Created: ruft.yaml{reset}")
    else:
        print(f"{yellow}Skipped: ruft.yaml (already exists){reset}")

    # Create .ruff.toml if it doesn't exist
    ruff_toml = project_root / ".ruff.toml"
    if not ruff_toml.exists():
        # Copy template
        template_path = Path(__file__).parent / "templates" / "ruff.toml"
        if template_path.exists():
            with open(template_path, encoding="utf-8") as f:
                content = f.read()
            with open(ruff_toml, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"{green}Created: .ruff.toml{reset}")
        else:
            # Fallback minimal config
            minimal_ruff = """# Ruff configuration
line-length = 120

[lint]
select = ["F", "E", "W", "I", "N", "UP", "ANN", "C4", "PIE", "RET", "SIM", "RUF"]
ignore = ["ANN002", "ANN003"]

[format]
quote-style = "double"
"""
            with open(ruff_toml, "w", encoding="utf-8") as f:
                f.write(minimal_ruff)
            print(f"{green}Created: .ruff.toml (minimal){reset}")
    else:
        print(f"{yellow}Skipped: .ruff.toml (already exists){reset}")

    print(f"\n{green}RUFT initialized! Run 'ruft' to start.{reset}")
    return 0
