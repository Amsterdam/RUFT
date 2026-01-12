"""Ruff formatting check with auto-fix support."""

import re
import subprocess

from ruft.checks import register_check
from ruft.checks.base import Check, CheckContext, CheckResult


@register_check("ruff_format")
class RuffFormatCheck(Check):
    """Ruff formatting check with auto-fix support."""

    name = "Ruff Formatter"
    can_auto_fix = True

    def get_command(self, ctx: CheckContext) -> list[str]:
        """Build the ruff format command."""
        cmd = [ctx.python_path, "-m", "ruff", "format"]

        if self.config.config_file:
            config_path = ctx.project_root / self.config.config_file
            if config_path.exists():
                cmd.extend(["--config", str(config_path)])

        cmd.extend(self.config.extra_args)
        cmd.append(".")

        return cmd

    def run(self, ctx: CheckContext) -> CheckResult:
        """Execute the ruff format check."""
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

            # ruff format returns 0 even when it reformats files
            # Check if any files were reformatted
            reformatted, _ = self._extract_format_stats(output)
            passed = result.returncode == 0

            return CheckResult(
                name=self.name,
                passed=passed,
                can_auto_fix=self.can_auto_fix,
                command=" ".join(cmd),
                output=output,
                error_count=reformatted if reformatted > 0 else error_count,
                error_details=f"{reformatted} file(s) reformatted" if reformatted > 0 else error_details,
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                passed=False,
                can_auto_fix=self.can_auto_fix,
                command=" ".join(cmd),
                output=f"Error running ruff format: {e}",
                error_count=1,
                error_details="execution error",
            )

    def _extract_format_stats(self, output: str) -> tuple[int, int]:
        """Extract formatting statistics from ruff format output."""
        reformatted = 0
        unchanged = 0

        lines = output.strip().split("\n") if output else []
        for line in lines:
            if "reformatted" in line.lower():
                match = re.search(r"(\d+) files? reformatted", line)
                if match:
                    reformatted = int(match.group(1))
            if "unchanged" in line.lower():
                match = re.search(r"(\d+) files? (?:left )?unchanged", line)
                if match:
                    unchanged = int(match.group(1))

        return reformatted, unchanged

    def parse_output(self, output: str) -> tuple[int, str]:
        """Parse output to extract error count."""
        reformatted, unchanged = self._extract_format_stats(output)
        if reformatted > 0:
            return reformatted, f"{reformatted} file(s) reformatted"
        return 0, ""

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
