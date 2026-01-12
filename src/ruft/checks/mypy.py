"""MyPy type checking."""

import re
import subprocess

from ruft.checks import register_check
from ruft.checks.base import Check, CheckContext, CheckResult


@register_check("mypy")
class MyPyCheck(Check):
    """MyPy static type checking."""

    name = "MyPy Type Check"
    can_auto_fix = False

    def get_command(self, ctx: CheckContext) -> list[str]:
        """Build the mypy command."""
        cmd = [ctx.python_path, "-m", "mypy"]

        if self.config.config_file:
            config_path = ctx.project_root / self.config.config_file
            if config_path.exists():
                cmd.extend(["--config-file", str(config_path)])

        cmd.extend(self.config.extra_args)
        cmd.append(".")

        return cmd

    def run(self, ctx: CheckContext) -> CheckResult:
        """Execute the mypy check."""
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
                output=f"Error running mypy: {e}",
                error_count=1,
                error_details="execution error",
            )

    def parse_output(self, output: str) -> tuple[int, str]:
        """Parse MyPy output to extract error count."""
        error_lines = [line for line in output.split("\n") if ": error:" in line]
        error_count = len(error_lines)

        error_details = ""
        if error_count > 0:
            # Get first few error types as summary
            error_types: set[str] = set()
            for line in error_lines[:3]:
                if ": error:" in line:
                    error_part = line.split(": error:")[1].strip()
                    bracket_match = re.search(r"\[([^\]]+)\]", error_part)
                    if bracket_match:
                        error_types.add(bracket_match.group(1))
                    else:
                        # Take first meaningful word
                        error_type = error_part.split(".")[0].split("(")[0].strip()
                        if error_type:
                            error_types.add(error_type[:20])  # Limit length
            error_details = ", ".join(list(error_types)[:2])

        return error_count, error_details

    @classmethod
    def is_available(cls) -> bool:
        """Check if mypy is installed."""
        try:
            result = subprocess.run(
                ["python", "-m", "mypy", "--version"],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
