"""Terminal output utilities for colorful, cross-platform display."""

import os
import sys


def is_git_hook_environment() -> bool:
    """Detect if we're running in a git hook or CI environment."""
    git_hook_indicators = [
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_AUTHOR_NAME",
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
    ]

    if any(os.environ.get(indicator) for indicator in git_hook_indicators):
        return True

    pre_commit_indicators = [
        "PRE_COMMIT",
        "PRE_COMMIT_HOME",
        "_PRE_COMMIT_HOOK_ID",
        "PRE_COMMIT_COLOR",
    ]
    if any(os.environ.get(indicator) for indicator in pre_commit_indicators):
        return True

    for env_var in os.environ:
        if "PRE_COMMIT" in env_var and "VSCODE" not in env_var:
            return True

    return bool(
        any("hook" in str(arg).lower() for arg in sys.argv if "vscode" not in str(arg).lower())
    )


def should_use_concise_mode() -> bool:
    """Determine if we should use concise output mode (for git hooks)."""
    return is_git_hook_environment() or os.environ.get("RUFT_CONCISE_MODE") == "1"


def supports_color() -> bool:
    """Check if the current terminal supports ANSI colors."""
    if os.environ.get("FORCE_COLOR", "").lower() in ("1", "true", "yes"):
        return True

    if os.environ.get("NO_COLOR", "").lower() in ("1", "true", "yes"):
        return False

    if any(os.environ.get(var) for var in ["MSYSTEM", "MINGW_PREFIX", "TERM"]):
        return True

    ci_environments = ("GITHUB_ACTIONS", "GITLAB_CI", "TRAVIS", "CIRCLECI")
    if any(os.environ.get(env) for env in ci_environments):
        return True

    if is_git_hook_environment():
        return True

    if os.name == "nt" and hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            handle = kernel32.GetStdHandle(-11)
            mode = wintypes.DWORD()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
            return True
        except Exception:
            pass

    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    LIGHT_GRAY = "\033[37m"

    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    DIM = "\033[2m"

    RESET = "\033[0m"

    @classmethod
    def disable_if_unsupported(cls) -> None:
        """Disable colors if the terminal doesn't support them."""
        if not supports_color():
            for attr in dir(cls):
                if not attr.startswith("_") and attr != "disable_if_unsupported":
                    setattr(cls, attr, "")


def colored_text(text: str, color: str, bold: bool = False) -> str:
    """Create colored text with optional bold styling."""
    if not supports_color() and not os.environ.get("FORCE_COLOR"):
        return text

    style = Colors.BOLD if bold else ""
    return f"{style}{color}{text}{Colors.RESET}"


def muted_text(text: str) -> str:
    """Create muted (gray/dim) text for less important information."""
    if not supports_color() and not os.environ.get("FORCE_COLOR"):
        return text

    return f"{Colors.DIM}{Colors.GRAY}{text}{Colors.RESET}"


def safe_emoji_text(emoji_text: str, plain_text: str) -> str:
    """Return emoji text if supported by terminal, otherwise plain text."""
    try:
        emoji_text.encode(sys.stdout.encoding or "utf-8")
        if supports_color():
            if "\u2705" in emoji_text:  # checkmark
                return colored_text(emoji_text, Colors.GREEN, bold=True)
            if "\u274c" in emoji_text:  # X mark
                return colored_text(emoji_text, Colors.RED, bold=True)
            if "\U0001f389" in emoji_text:  # party
                return colored_text(emoji_text, Colors.CYAN, bold=True)
            return colored_text(emoji_text, Colors.YELLOW, bold=True)
        return emoji_text
    except (UnicodeEncodeError, AttributeError, LookupError):
        if supports_color():
            if "PASSED" in plain_text:
                return colored_text(plain_text, Colors.GREEN, bold=True)
            if "FAILED" in plain_text:
                return colored_text(plain_text, Colors.RED, bold=True)
            return colored_text(plain_text, Colors.YELLOW, bold=True)
        return plain_text


def safe_symbol(unicode_symbol: str, ascii_fallback: str) -> str:
    """Return Unicode symbol if supported, otherwise ASCII fallback."""
    try:
        unicode_symbol.encode(sys.stdout.encoding or "utf-8")
        return unicode_symbol
    except (UnicodeEncodeError, AttributeError, LookupError):
        return ascii_fallback


def safe_arrow() -> str:
    """Return Unicode arrow if supported, otherwise ASCII fallback."""
    return safe_symbol("\u2192 ", "-> ")


def colorized_status_message(message: str, is_success: bool, is_warning: bool = False) -> str:
    """Create a colorized status message based on the status type."""
    if is_success:
        prefix = safe_symbol("\u2713 ", "[OK] ")
        if supports_color():
            return colored_text(f"{prefix}{message}", Colors.GREEN, bold=True)
        return f"{prefix}{message}"
    if is_warning:
        prefix = safe_symbol("\u26a0 ", "[INFO] ")
        if supports_color():
            return colored_text(f"{prefix}{message}", Colors.YELLOW, bold=True)
        return f"{prefix}{message}"
    prefix = safe_symbol("\u2717 ", "[ERROR] ")
    if supports_color():
        return colored_text(f"{prefix}{message}", Colors.RED, bold=True)
    return f"{prefix}{message}"
