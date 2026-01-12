"""Pytest test runner check."""

import re
import subprocess

from ruft.checks import register_check
from ruft.checks.base import Check, CheckContext, CheckResult


@register_check("pytest")
class PytestCheck(Check):
    """Pytest test runner."""

    name = "Tests"
    can_auto_fix = False

    def get_command(self, ctx: CheckContext) -> list[str]:
        """Build the pytest command."""
        cmd = [ctx.python_path, "-m", "pytest"]

        # Add test directory from config or default
        test_dir = getattr(self.config, "test_dir", None) or "tests"
        cmd.append(test_dir)

        # Add verbosity
        if ctx.verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        cmd.extend(self.config.extra_args)

        return cmd

    def run(self, ctx: CheckContext) -> CheckResult:
        """Execute the pytest check."""
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

            # Update name with test count if available
            name = self.name
            test_count = self._extract_test_count(output)
            if test_count > 0:
                name = f"Tests ({test_count} tests)"

            return CheckResult(
                name=name,
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
                output=f"Error running pytest: {e}",
                error_count=1,
                error_details="execution error",
            )

    def _extract_test_count(self, output: str) -> int:
        """Extract total test count from pytest output."""
        # Look for "X collected" or "X passed"
        collected = re.search(r"(\d+) collected", output)
        if collected:
            return int(collected.group(1))

        passed = re.search(r"(\d+) passed", output)
        if passed:
            return int(passed.group(1))

        return 0

    def parse_output(self, output: str) -> tuple[int, str]:
        """Parse pytest output for failures and errors."""
        error_count = 0
        error_details = ""

        # Look for pytest format
        failed = re.search(r"(\d+) failed", output)
        errors = re.search(r"(\d+) error", output)
        passed = re.search(r"(\d+) passed", output)
        collected = re.search(r"(\d+) collected", output)

        if failed:
            error_count += int(failed.group(1))
            error_details = "test failures"
        if errors:
            error_count += int(errors.group(1))
            error_details = error_details or "test errors"

        # Add pass/total info
        if collected and (failed or errors):
            total = int(collected.group(1))
            passed_count = int(passed.group(1)) if passed else 0
            error_details = f"{passed_count}/{total} passed, {error_details}"

        return error_count, error_details

    @classmethod
    def is_available(cls) -> bool:
        """Check if pytest is installed."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--version"],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
