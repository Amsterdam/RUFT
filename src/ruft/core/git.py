"""Git operations for RUFT workflow."""

import hashlib
import subprocess
from pathlib import Path

from ruft.output.terminal import Colors, supports_color


class GitOps:
    """Git operations helper."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize with project root."""
        self.project_root = project_root or Path.cwd()

    def _run(self, *args: str, capture: bool = True) -> tuple[int, str]:
        """Run a git command and return exit code and output."""
        try:
            result = subprocess.run(
                ["git", *args],
                capture_output=capture,
                text=True,
                cwd=self.project_root,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            output = ""
            if capture:
                output = (result.stdout or "") + (result.stderr or "")
            return result.returncode, output
        except Exception as e:
            return 1, f"Error running git: {e}"

    def is_git_repo(self) -> bool:
        """Check if we're in a git repository."""
        code, _ = self._run("rev-parse", "--git-dir")
        return code == 0

    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        code, output = self._run("status", "--porcelain")
        return code == 0 and len(output.strip()) > 0

    def get_diff_hash(self) -> str:
        """Get a hash of the current git diff to detect changes."""
        code, output = self._run("diff")
        if code != 0:
            return ""
        return hashlib.md5(output.encode()).hexdigest()

    def add_all(self) -> bool:
        """Stage all changes."""
        code, _ = self._run("add", ".")
        return code == 0

    def commit(self, message: str) -> bool:
        """Commit staged changes with the given message."""
        blue = Colors.BLUE if supports_color() else ""
        cyan = Colors.CYAN if supports_color() else ""
        green = Colors.GREEN if supports_color() else ""
        red = Colors.RED if supports_color() else ""
        reset = Colors.RESET if supports_color() else ""

        print(f"{blue}[*] Committing changes: {message}{reset}")

        # Stage all changes
        print(f"{cyan}[>] Staging changes...{reset}")
        if not self.add_all():
            print(f"{red}[X] Failed to stage changes{reset}")
            return False

        # Commit
        print(f"{cyan}[>] Creating commit...{reset}")
        code, output = self._run("commit", "-m", message)

        if code != 0:
            print(f"{red}[X] Failed to commit changes{reset}")
            print(f"{red}    Error: {output.strip()}{reset}")
            return False

        print(f"{green}[+] Changes committed successfully{reset}")
        return True

    def push(self) -> int:
        """Push changes to remote. Returns exit code."""
        blue = Colors.BLUE if supports_color() else ""
        green = Colors.GREEN if supports_color() else ""
        red = Colors.RED if supports_color() else ""
        reset = Colors.RESET if supports_color() else ""

        print(f"{blue}[>] Pushing changes...{reset}")
        code, output = self._run("push", capture=False)

        if code != 0:
            print(f"{red}[X] Failed to push changes{reset}")
            return 1

        print(f"{green}[+] Changes pushed successfully!{reset}")
        return 0
