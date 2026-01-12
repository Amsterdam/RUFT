"""Progress indicators and spinners for long-running operations."""

import itertools
import sys
import threading
import time
from typing import Callable

from ruft.output.terminal import Colors, supports_color


class Spinner:
    """Animated spinner for long-running operations."""

    def __init__(self, message: str) -> None:
        """Initialize spinner with a message."""
        self.message = message
        self.spinner = itertools.cycle(["|", "/", "-", "\\"])
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.use_colors = supports_color()

    def _spin(self) -> None:
        """Show animated spinner while operation is running."""
        while not self.stop_event.is_set():
            try:
                spinner_char = next(self.spinner)
                if self.use_colors:
                    print(
                        f"\r{Colors.CYAN}[>] {self.message}... {spinner_char}{Colors.RESET}",
                        end="",
                        flush=True,
                    )
                else:
                    print(f"\r[>] {self.message}... {spinner_char}", end="", flush=True)
            except (UnicodeEncodeError, Exception):
                print(f"\r[>] {self.message}...", end="", flush=True)
            time.sleep(0.2)

    def start(self) -> None:
        """Start the spinner animation."""
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()

    def stop(self) -> None:
        """Stop the spinner animation."""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=0.5)
        # Clear the spinner line
        if self.use_colors:
            print(f"\r{Colors.CYAN}[>] {self.message}...{Colors.RESET}", end="", flush=True)
        else:
            print(f"\r[>] {self.message}...", end="", flush=True)
        sys.stdout.flush()


def with_spinner(message: str) -> Callable:
    """Decorator to show a spinner while a function runs."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
            spinner = Spinner(message)
            spinner.start()
            try:
                return func(*args, **kwargs)
            finally:
                spinner.stop()

        return wrapper

    return decorator


def print_status(message: str, color: str = "") -> None:
    """Print a status message with optional color."""
    if color and supports_color():
        print(f"{color}{message}{Colors.RESET}")
    else:
        print(message)
