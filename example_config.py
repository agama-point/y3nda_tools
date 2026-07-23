"""Print the y3nda configuration and optionally mirror output to a log file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lib.wrapp_log import console_log, get_project_directory, load_config

PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load and display the y3nda configuration.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "y3nda_config.json",
        help="Path to configuration JSON (default: %(default)s).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
        project_directory = get_project_directory(PROJECT_ROOT, config)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    with console_log(project_directory, Path(__file__).name, bool(config["log"])):
        print(f"Configuration file: {args.config.resolve()}")
        print(f"Project directory:  {project_directory}")
        print(f"Console logging:    {config['log']}")
        print("\nConfiguration values:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
        if config["log"]:
            print(f"\nThis console output was saved to: {project_directory / 'log.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
