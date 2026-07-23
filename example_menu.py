"""A minimal interactive menu for reading and saving a .env file."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from dotenv import dotenv_values, set_key

from lib.terminal import Terminal
from lib.wrapp_log import console_log, get_project_directory, load_config

PROJECT_ROOT = Path(__file__).resolve().parent
VALID_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactively edit a .env file.")
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
    return parser.parse_args()


def load_values(env_path: Path, t: Terminal) -> dict[str, str]:
    if not env_path.exists():
        t.y(f"No .env file yet: {env_path}")
        return {}
    values = dotenv_values(env_path)
    return {key: value or "" for key, value in values.items()}


def show_values(values: dict[str, str], t: Terminal) -> None:
    if not values:
        t.y("No values loaded.")
        return
    for key in sorted(values):
        print(f"{key}={values[key]}")


def save_values(env_path: Path, values: dict[str, str], t: Terminal) -> None:
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.touch(exist_ok=True)
    for key, value in values.items():
        set_key(str(env_path), key, value, quote_mode="auto")
    t.g(f"Saved {len(values)} value(s) to {env_path}.")


def run_menu(env_path: Path) -> int:
    t = Terminal()
    values: dict[str, str] = {}

    while True:
        print("\n" + "-" * 32)
        t.g("dot_env menu")
        print("-" * 32)
        print(f"{t.color('y', 'L')}oad .env")
        print(f"{t.color('y', 'S')}how loaded values")
        print(f"{t.color('y', 'A')}dd or change a value")
        print(f"{t.color('y', 'W')}rite values to .env")
        print(f"{t.color('y', 'E')}xit")
        prompt = f"{t.color('y', 'Choose an option')} [L/S/A/W/E]: "
        choice = input(prompt).strip().lower()

        if choice == "l":
            values = load_values(env_path, t)
            t.g(f"Loaded {len(values)} value(s).")
        elif choice == "s":
            show_values(values, t)
        elif choice == "a":
            key = input("Key: ").strip()
            if not VALID_KEY.fullmatch(key):
                t.y("Invalid key. Use letters, digits, and underscores; do not start with a digit.")
                continue
            values[key] = input("Value: ")
            t.g(f"Stored {key} in memory. Choose Save to write it to disk.")
        elif choice == "w":
            save_values(env_path, values, t)
        elif choice == "e":
            t.g("Goodbye.")
            return 0
        else:
            t.y("Unknown option. Choose L, S, A, W, or E.")


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
        return run_menu(env_path)


if __name__ == "__main__":
    raise SystemExit(main())
