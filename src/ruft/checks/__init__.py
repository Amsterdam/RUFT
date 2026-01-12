"""Quality check plugins and registry."""

from typing import Type

from ruft.checks.base import Check, CheckResult

# Registry of built-in checks
_BUILTIN_CHECKS: dict[str, Type[Check]] = {}


def register_check(name: str):  # type: ignore[no-untyped-def]
    """Decorator to register a check class."""

    def decorator(cls: Type[Check]) -> Type[Check]:
        _BUILTIN_CHECKS[name] = cls
        return cls

    return decorator


def get_check(name: str) -> Type[Check] | None:
    """Get a check class by name."""
    return _BUILTIN_CHECKS.get(name)


def list_checks() -> list[str]:
    """List all registered check names."""
    return list(_BUILTIN_CHECKS.keys())


def get_all_checks() -> dict[str, Type[Check]]:
    """Get all registered checks."""
    return _BUILTIN_CHECKS.copy()


# Import check modules to trigger registration
from ruft.checks import custom, mypy, pytest_check, ruff_format, ruff_lint  # noqa: E402, F401

__all__ = [
    "Check",
    "CheckResult",
    "get_all_checks",
    "get_check",
    "list_checks",
    "register_check",
]
