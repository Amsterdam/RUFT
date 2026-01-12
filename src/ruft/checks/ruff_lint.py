"""Ruff linting check with auto-fix support."""

import re
import subprocess
from pathlib import Path

from ruft.checks import register_check
from ruft.checks.base import Check, CheckContext, CheckResult


@register_check("ruff_lint")
class RuffLintCheck(Check):
    """Ruff linting check with auto-fix support."""

    name = "Ruff Style Check"
    can_auto_fix = True

    def get_command(self, ctx: CheckContext) -> list[str]:
        """Build the ruff check command."""
        cmd = [ctx.python_path, "-m", "ruff", "check", "--fix"]

        if self.config.config_file:
            config_path = ctx.project_root / self.config.config_file
            if config_path.exists():
                cmd.extend(["--config", str(config_path)])

        cmd.extend(self.config.extra_args)
        cmd.append(".")

        return cmd

    def run(self, ctx: CheckContext) -> CheckResult:
        """Execute the ruff lint check."""
        cmd = self.get_command(ctx)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=ctx.project_root,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

            output = (result.stdout or "") + (result.stderr or "")
            error_count, error_details = self.parse_output(output)

            return CheckResult(
                name=self.name,
                passed=result.returncode == 0,
                can_auto_fix=self.can_auto_fix,
                command=" ".join(cmd),
                output=output,
                error_count=error_count,
                error_details=error_details,
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                passed=False,
                can_auto_fix=self.can_auto_fix,
                command=" ".join(cmd),
                output=f"Error running ruff: {e}",
                error_count=1,
                error_details="execution error",
            )

    def parse_output(self, output: str) -> tuple[int, str]:
        """Parse Ruff output to extract error count."""
        error_count = 0
        error_details = ""

        # Look for "Found X errors" pattern
        found_match = re.search(r"Found (\d+) errors?", output)
        if found_match:
            error_count = int(found_match.group(1))
        else:
            # Fallback: count error lines
            error_lines = [
                line
                for line in output.split("\n")
                if line.strip() and ".py:" in line and not line.startswith("Found")
            ]
            error_count = len(error_lines)

        if error_count > 0:
            # Look for fixable info
            fixed_remaining = re.search(r"Found \d+ errors \((\d+) fixed, (\d+) remaining\)", output)
            if fixed_remaining:
                fixed = int(fixed_remaining.group(1))
                remaining = int(fixed_remaining.group(2))
                error_details = f"{fixed} auto-fixed, {remaining} remaining"
            else:
                fixable_match = re.search(r"(\d+) fixable", output)
                if fixable_match:
                    fixable = int(fixable_match.group(1))
                    if fixable > 0:
                        error_details = "all auto-fixable" if fixable == error_count else f"{fixable} auto-fixable"

        return error_count, error_details

    @classmethod
    def is_available(cls) -> bool:
        """Check if ruff is installed."""
        try:
            result = subprocess.run(
                ["python", "-m", "ruff", "--version"],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
