"""Main RUFT orchestrator."""

import sys
import time
from pathlib import Path

from ruft.checks import get_check
from ruft.checks.base import Check, CheckContext, CheckResult
from ruft.config import CheckConfig, RuftConfig
from ruft.core.git import GitOps
from ruft.core.venv import ensure_venv
from ruft.output.progress import Spinner
from ruft.output.reporter import print_failure_instructions, print_final_report, print_success_message
from ruft.output.terminal import Colors, supports_color


class Runner:
    """Main RUFT orchestrator."""

    def __init__(self, config: RuftConfig) -> None:
        """Initialize runner with configuration."""
        self.config = config
        self.git = GitOps()

    def run(self, dry_run: bool = False, no_push: bool = False, verbose: bool = False) -> int:
        """Execute the quality check workflow.

        Returns exit code (0 for success, 1 for failure).
        """
        project_root = Path.cwd()

        bold = Colors.BOLD if supports_color() else ""
        cyan = Colors.CYAN if supports_color() else ""
        yellow = Colors.YELLOW if supports_color() else ""
        red = Colors.RED if supports_color() else ""
        reset = Colors.RESET if supports_color() else ""

        print(f"{bold}>> Starting RUFT Quality Check Workflow{reset}")
        print("=" * 60)

        # Check if we're in a git repository
        if not self.git.is_git_repo():
            print(f"{red}[X] Not in a git repository{reset}")
            return 1

        # Handle uncommitted changes
        if not self._handle_uncommitted_changes(dry_run):
            return 1

        # Setup virtual environment
        python_path = ensure_venv(project_root)

        # Build check list from config
        checks = self._build_check_list()
        if not checks:
            print(f"{yellow}[!] No checks enabled{reset}")
            return 0

        # Create context
        ctx = CheckContext(
            project_root=project_root,
            python_path=python_path,
            dry_run=dry_run,
            verbose=verbose,
        )

        # Run iteration loop
        max_iterations = self.config.settings.max_iterations
        all_results: list[CheckResult] = []

        for iteration in range(1, max_iterations + 1):
            print(f"\n{bold}>> Iteration {iteration}{reset}")
            print("-" * 40)

            # Get git state before checks
            diff_hash_before = self.git.get_diff_hash()

            # Run all checks
            results = self._run_checks(checks, ctx)
            all_results = results  # Keep latest results

            # Check if auto-fixes were applied
            diff_hash_after = self.git.get_diff_hash()
            made_fixes = diff_hash_before != diff_hash_after

            if made_fixes:
                print(f"{yellow}[!] Auto-fixes applied{reset}")
                if not dry_run and self.config.settings.auto_commit_fixes:
                    prefix = self.config.settings.commit_message_prefix
                    message = f"{prefix} iteration {iteration}"
                    if not self.git.commit(message):
                        # Commit failed but continue
                        pass
                elif dry_run:
                    print(f"{yellow}[DRY RUN] Would commit auto-fixes{reset}")
            else:
                print(f"{cyan}[i] No auto-fixes applied, proceeding to final report{reset}")
                break

        # Final report
        failed_checks = print_final_report(all_results)

        if failed_checks:
            print_failure_instructions(failed_checks)
            return 1

        print_success_message()

        # Handle push
        return self._handle_push(dry_run, no_push)

    def _handle_uncommitted_changes(self, dry_run: bool) -> bool:
        """Handle uncommitted changes. Returns True to continue, False to abort."""
        yellow = Colors.YELLOW if supports_color() else ""
        cyan = Colors.CYAN if supports_color() else ""
        reset = Colors.RESET if supports_color() else ""

        if not self.git.has_uncommitted_changes():
            return True

        print(f"{yellow}[!] Uncommitted changes detected{reset}")

        if dry_run:
            print(f"{yellow}[DRY RUN] Would prompt to commit uncommitted changes{reset}")
            return True

        # Prompt user
        try:
            response = input(f"{cyan}Commit all changes before quality checks? (y/N): {reset}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{yellow}[!] Input cancelled, proceeding with uncommitted changes{reset}")
            return True

        if response in ("y", "yes"):
            try:
                message = input(f"{cyan}Enter commit message: {reset}").strip()
            except (EOFError, KeyboardInterrupt):
                message = ""

            if not message:
                message = "Manual changes before quality checks"

            if not self.git.commit(message):
                return False
        else:
            print(f"{yellow}[i] Proceeding with uncommitted changes{reset}")

        return True

    def _build_check_list(self) -> list[Check]:
        """Build list of enabled checks from configuration."""
        checks: list[Check] = []

        for name, check_config in self.config.checks.items():
            if not check_config.enabled:
                continue

            # Get check class from registry
            # For custom checks, the name starts with "custom_"
            check_type = "custom" if name.startswith("custom_") else name
            check_class = get_check(check_type)

            if check_class is None:
                continue

            if not check_class.is_available():
                yellow = Colors.YELLOW if supports_color() else ""
                reset = Colors.RESET if supports_color() else ""
                print(f"{yellow}[!] Check '{name}' not available (missing dependency){reset}")
                continue

            checks.append(check_class(check_config))

        return checks

    def _run_checks(self, checks: list[Check], ctx: CheckContext) -> list[CheckResult]:
        """Run all checks and return results."""
        results: list[CheckResult] = []

        for check in checks:
            result = self._run_single_check(check, ctx)
            results.append(result)

        return results

    def _run_single_check(self, check: Check, ctx: CheckContext) -> CheckResult:
        """Run a single check with progress indication."""
        cyan = Colors.CYAN if supports_color() else ""
        green = Colors.GREEN if supports_color() else ""
        red = Colors.RED if supports_color() else ""
        reset = Colors.RESET if supports_color() else ""

        print(f"{cyan}[>] Running {check.name}...{reset}", end="", flush=True)
        start_time = time.time()

        # Use spinner for tests (they take longer)
        use_spinner = "test" in check.name.lower()
        spinner = None

        if use_spinner:
            spinner = Spinner(check.name)
            spinner.start()

        try:
            result = check.run(ctx)
        finally:
            if spinner:
                spinner.stop()

        duration = time.time() - start_time

        # Print result
        if result.passed:
            status = f" {green}[+] PASSED"
            if duration > 1.0:
                status += f" ({duration:.1f}s)"
        else:
            status = f" {red}[X] FAILED"
            if result.error_count > 0:
                status += f" - {result.error_count} error{'s' if result.error_count != 1 else ''}"
                if result.error_details:
                    status += f" ({result.error_details})"

        print(f"{status}{reset}")

        return result

    def _handle_push(self, dry_run: bool, no_push: bool) -> int:
        """Handle pushing changes. Returns exit code."""
        yellow = Colors.YELLOW if supports_color() else ""
        reset = Colors.RESET if supports_color() else ""

        if no_push:
            print(f"{yellow}[*] Changes ready to push (use 'git push' manually){reset}")
            return 0

        if dry_run:
            print(f"{yellow}[DRY RUN] Would push changes{reset}")
            return 0

        if self.config.git.auto_push:
            return self.git.push()

        print(f"{yellow}[*] Changes ready to push (use 'git push' manually){reset}")
        return 0
