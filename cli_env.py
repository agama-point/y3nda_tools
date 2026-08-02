"""Read values from a .env file with python-dotenv.

Compatible with Python 3.6 and newer.
"""

import argparse
import os
import sys
from contextlib import contextmanager
from pathlib import Path


def _fallback_dotenv_values(env_path):
    """Read simple KEY=VALUE entries without the optional python-dotenv package."""

    values = {}
    with Path(env_path).open(encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].lstrip()
            if "=" not in line:
                values[line] = None
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            if key:
                values[key] = value
    return values


def _fallback_load_dotenv(env_path, override=False):
    """Load basic .env values into the current process environment."""

    for key, value in _fallback_dotenv_values(env_path).items():
        if value is not None and (override or key not in os.environ):
            os.environ[key] = value


try:
    from dotenv import dotenv_values, load_dotenv
except ImportError:
    DOTENV_AVAILABLE = False
    dotenv_values = _fallback_dotenv_values
    load_dotenv = _fallback_load_dotenv
else:
    DOTENV_AVAILABLE = True

try:
    from lib.wrapp_log import console_log, get_project_directory, load_config
except ImportError:
    WRAPP_LOG_AVAILABLE = False

    @contextmanager
    def console_log(_project_directory, _program_name, _enabled):
        """Provide a no-op replacement when the optional helper is absent."""

        yield
else:
    WRAPP_LOG_AVAILABLE = True


PROJECT_ROOT = Path(__file__).resolve().parent
__version__ = "0.26.01"


def parse_args() -> argparse.Namespace:
    """Parse command-line options for reading a .env file."""

    parser = argparse.ArgumentParser(
        description="Read and display values from a .env file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s {0} (Python 3.6+)".format(__version__),
        help="Show the program version and exit.",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=PROJECT_ROOT / "yt.json",
        help="Path to configuration JSON.",
    )
    parser.add_argument(
        "-e",
        "--env-file",
        type=Path,
        help="Path to .env; defaults to .env in the configured project directory.",
    )
    parser.add_argument(
        "-l",
        "--load",
        action="store_true",
        help="Also load values into this process environment without replacing existing variables.",
    )
    display_group = parser.add_mutually_exclusive_group()
    display_group.add_argument(
        "-k",
        "--key",
        metavar="NAME",
        help="Show only the value of NAME.",
    )
    display_group.add_argument(
        "--names",
        action="store_true",
        help="Show only variable names, not their values.",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Do not mirror this command's output to the project log file.",
    )
    return parser.parse_args()


def print_values(values, key=None, names_only=False) -> int:
    """Print selected dotenv values and return a suitable process status."""

    if key is not None:
        if key not in values:
            print("No value named {0!r} in the .env file.".format(key), file=sys.stderr)
            return 1
        value = values[key]
        print("{0}={1}".format(key, value if value is not None else ""))
        return 0

    if not values:
        print("  (file is empty)")
        return 0

    for name, value in values.items():
        if names_only:
            print("  {0}".format(name))
        else:
            print("  {0}={1}".format(name, value if value is not None else ""))
    return 0


def get_project_settings(config_path: Path):
    """Return the project directory and logging state, with a standalone fallback."""

    if not WRAPP_LOG_AVAILABLE:
        print(
            "Warning: optional lib.wrapp_log is unavailable; using the current directory and no log file.",
            file=sys.stderr,
        )
        return Path.cwd().resolve(), False

    try:
        config = load_config(config_path)
        project_directory = get_project_directory(PROJECT_ROOT, config)
    except ValueError as error:
        print("Error: {0}".format(error), file=sys.stderr)
        return None, False
    return project_directory, bool(config["log"])


def print_optional_dependency_warnings() -> None:
    """Explain when the command is using its dependency-free fallback."""

    if not DOTENV_AVAILABLE:
        print(
            "Warning: optional python-dotenv is unavailable; using basic .env parsing.",
            file=sys.stderr,
        )


def main() -> int:
    args = parse_args()
    print_optional_dependency_warnings()
    project_directory, logging_enabled = get_project_settings(args.config)
    if project_directory is None:
        return 1

    env_path = args.env_file.resolve() if args.env_file else project_directory / ".env"
    with console_log(project_directory, Path(__file__).name, logging_enabled and not args.no_log):
        if not env_path.is_file():
            print("No .env file found: {0}".format(env_path), file=sys.stderr)
            return 1

        values = dotenv_values(env_path)
        if args.load:
            load_dotenv(env_path, override=False)
            print("Values were loaded into this process (existing variables were kept).")

        if args.key is None:
            heading = "Variable names in" if args.names else "Values in"
            print("{0} {1}:".format(heading, env_path))
        return print_values(values, key=args.key, names_only=args.names)


if __name__ == "__main__":
    raise SystemExit(main())
