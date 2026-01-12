"""Base class for quality checks."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ruft.config import CheckConfig


@dataclass
class CheckResult:
    """Result of running a quality check."""

    name: str
    passed: bool
    can_auto_fix: bool
    command: str
    output: str
    error_count: int = 0
    error_details: str = ""


@dataclass
class CheckContext:
    """Context passed to checks during execution."""

    project_root: Path
    python_path: str
    dry_run: bool = False
    verbose: bool = False
    extra_args: list[str] = field(default_factory=list)


class Check(ABC):
    """Base class for all quality checks."""

    name: str = "Unnamed Check"
    can_auto_fix: bool = False

    def __init__(self, config: "CheckConfig") -> None:
        """Initialize the check with configuration."""
        self.config = config

    @abstractmethod
    def run(self, ctx: CheckContext) -> CheckResult:
        """Execute the check and return result."""
        ...

    def parse_output(self, output: str) -> tuple[int, str]:
        """Parse output to extract error count and details.

        Returns:
            Tuple of (error_count, error_details_string)
        """
        return 0, ""

    @classmethod
    def is_available(cls) -> bool:
        """Check if this check's dependencies are available."""
        return True

    def get_command(self, ctx: CheckContext) -> list[str]:
        """Get the command to run for this check.

        Override this in subclasses to customize the command.
        """
        return []
