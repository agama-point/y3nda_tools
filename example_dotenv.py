"""Load and display values from a .env file with python-dotenv."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

from lib.wrapp_log import console_log, get_project_directory, load_config

PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read and display a .env file.")
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "y3nda_config.json",
        help="Path to configuration JSON (default: %(default)s).",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Path to .env. Defaults to .env in the configured project directory.",
    )
    parser.add_argument(
        "--load",
        action="store_true",
        help="Also load the values into this process environment.",
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

    env_path = args.env_file.resolve() if args.env_file else project_directory / ".env"
    with console_log(project_directory, Path(__file__).name, bool(config["log"])):
        if not env_path.is_file():
            print(f"No .env file found: {env_path}", file=sys.stderr)
            return 1

        values = dotenv_values(env_path)
        if args.load:
            load_dotenv(env_path, override=False)
            print("Values were loaded into this process (existing variables were kept).")

        print(f"Values in {env_path}:")
        if not values:
            print("  (file is empty)")
        for key, value in values.items():
            print(f"  {key}={value if value is not None else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
