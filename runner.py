"""Command-line adapter for validated project Python command flows."""

import argparse
import sys
from pathlib import Path

from lib.wrapp_run import FlowError, FlowRunner
from lib.wrapp_log import get_project_directory, load_config


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_FLOW_PATH = Path("flow_example.txt")
CONFIG_PATH = PROJECT_ROOT / "yt.json"


def working_directory_help() -> str:
    """Return a help-text summary of the configured working directory."""

    try:
        config = load_config(CONFIG_PATH)
    except ValueError as error:
        return (
            "Working-directory configuration:\n"
            "  Configuration file: {0}\n"
            "  Warning: cannot read configuration ({1})\n"
            "  Flow lookup order: project root, then the configured working directory."
        ).format(CONFIG_PATH, error)

    subdir = str(config["subdir"])
    working_directory = PROJECT_ROOT / subdir
    logging_state = "enabled" if config["log"] else "disabled"
    return (
        "Working-directory configuration from yt.json:\n"
        "  Configuration file: {0}\n"
        "  subdir: {1}\n"
        "  Working directory: {2}\n"
        "  Project logging: {3}\n"
        "  Flow lookup order: project root, then working directory."
    ).format(CONFIG_PATH, subdir, working_directory, logging_state)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run validated project Python commands from a text file.",
        epilog=working_directory_help(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("flow_file", nargs="?", type=Path, default=DEFAULT_FLOW_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        config = load_config(CONFIG_PATH)
        working_directory = get_project_directory(PROJECT_ROOT, config)
        flow_runner = FlowRunner(PROJECT_ROOT, flow_directories=(working_directory,))
        flow_path = flow_runner.resolve_flow_path(arguments.flow_file)
        return flow_runner.run(flow_path, flow_runner.load(flow_path), arguments.dry_run)
    except (FlowError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nFlow interrupted by user.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
