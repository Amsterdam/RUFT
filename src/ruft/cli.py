"""RUFT Command Line Interface."""

import argparse
import sys
from pathlib import Path

from ruft import __version__
from ruft.config import create_default_config, load_config
from ruft.core.runner import Runner


def main() -> int:
    """Main entry point for RUFT CLI."""
    parser = argparse.ArgumentParser(
        prog="ruft",
        description="RUFT - Ruff-based Universal Fixer Tool: A transparent quality check and auto-fix workflow",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )

    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Run checks and commit fixes, but don't push",
    )

    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize RUFT config files in current directory",
    )

    parser.add_argument(
        "--check",
        nargs="*",
        metavar="CHECK",
        help="Run specific checks only (e.g., --check ruff_lint ruff_format)",
    )

    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        metavar="CONFIG",
        help="Path to ruft.yaml configuration file",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    # Handle --init
    if args.init:
        return create_default_config(Path.cwd())

    # Load configuration
    config = load_config(args.config)

    # Filter checks if --check specified
    if args.check is not None:
        if len(args.check) == 0:
            # --check with no args: list available checks
            print("Available checks:")
            for name, check_config in config.checks.items():
                status = "enabled" if check_config.enabled else "disabled"
                print(f"  {name}: {status}")
            return 0

        # Disable checks not in the list
        for name in list(config.checks.keys()):
            if name not in args.check:
                config.checks[name].enabled = False

    # Run workflow
    runner = Runner(config)
    return runner.run(
        dry_run=args.dry_run,
        no_push=args.no_push,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    sys.exit(main())
