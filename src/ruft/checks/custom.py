"""Custom command runner for user-defined checks."""

import subprocess

from ruft.checks import register_check
from ruft.checks.base import Check, CheckContext, CheckResult


@register_check("custom")
class CustomCheck(Check):
    """Run arbitrary shell commands as checks."""

    name = "Custom Check"
    can_auto_fix = False

    def __init__(self, config) -> None:  # type: ignore[no-untyped-def]
        """Initialize custom check with name from config."""
        super().__init__(config)
        # Use name from config if provided
        if hasattr(config, "name") and config.name:
            self.name = config.name
        # Use can_auto_fix from config if provided
        if hasattr(config, "can_auto_fix"):
            self.can_auto_fix = config.can_auto_fix

    def run(self, ctx: CheckContext) -> CheckResult:
        """Execute the custom command."""
        if not self.config.command:
            return CheckResult(
                name=self.name,
                passed=False,
                can_auto_fix=False,
                command="",
                output="No command specified",
                error_count=1,
                error_details="missing command",
            )

        command = self.config.command

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=ctx.project_root,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

            output = (result.stdout or "") + (result.stderr or "")

            return CheckResult(
                name=self.name,
                passed=result.returncode == 0,
                can_auto_fix=self.can_auto_fix,
                command=command,
                output=output,
                error_count=0 if result.returncode == 0 else 1,
                error_details="" if result.returncode == 0 else "command failed",
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                passed=False,
                can_auto_fix=self.can_auto_fix,
                command=command,
                output=f"Error running command: {e}",
                error_count=1,
                error_details="execution error",
            )

    @classmethod
    def is_available(cls) -> bool:
        """Custom checks are always available."""
        return True
