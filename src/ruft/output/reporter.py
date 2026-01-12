"""Final status report formatting."""

import re
from typing import TYPE_CHECKING

from ruft.output.terminal import Colors, colored_text, supports_color

if TYPE_CHECKING:
    from ruft.checks.base import CheckResult


def print_final_report(results: list["CheckResult"]) -> list["CheckResult"]:
    """Print the final status report and return failed checks."""
    print(f"\n{Colors.BOLD}>> Final Status Report{Colors.RESET}" if supports_color() else "\n>> Final Status Report")
    print("=" * 60)

    failed_checks: list[CheckResult] = []

    for check in results:
        if check.passed:
            status = f"{Colors.GREEN}[+] PASSED" if supports_color() else "[+] PASSED"
            # Try to show test count for test checks
            if "test" in check.name.lower() and check.output:
                test_count_match = re.search(r"(\d+) (collected|passed)", check.output)
                if test_count_match:
                    status += f" - {test_count_match.group(1)} tests"
        else:
            status = f"{Colors.RED}[X] FAILED" if supports_color() else "[X] FAILED"
            if check.error_count > 0:
                status += f" - Found {check.error_count} error{'s' if check.error_count != 1 else ''}"
                if check.error_details:
                    status += f" ({check.error_details})"
            failed_checks.append(check)

        reset = Colors.RESET if supports_color() else ""
        print(f"  {check.name}: {status}{reset}")

    return failed_checks


def print_failure_instructions(failed_checks: list["CheckResult"]) -> None:
    """Print instructions for fixing failed checks."""
    if not failed_checks:
        return

    red = Colors.RED if supports_color() else ""
    yellow = Colors.YELLOW if supports_color() else ""
    cyan = Colors.CYAN if supports_color() else ""
    reset = Colors.RESET if supports_color() else ""

    print(f"\n{red}[X] Some checks failed and cannot be auto-fixed:{reset}")
    print(f"{yellow}To investigate and fix manually, run:{reset}")
    for check in failed_checks:
        print(f"  {cyan}{check.command}{reset}  # Fix {check.name}")
    print(f"\n{yellow}Fix these issues and run ruft again.{reset}")


def print_success_message() -> None:
    """Print success message when all checks pass."""
    green = Colors.GREEN if supports_color() else ""
    reset = Colors.RESET if supports_color() else ""
    print(f"\n{green}[+] All quality checks passed!{reset}")
