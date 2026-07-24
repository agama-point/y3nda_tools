"""Main command-line entry point for the small y3nda cipher project.

The command reads the project subdirectory from ``y3nda_config.json`` and
prints the transformed value.  It deliberately does not overwrite
``data.txt``: redirect its output or copy the result there only when that is
really intended.
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import dotenv_values

from crypto_agama.agama_cipher import caesar_encrypt, toggle_xor
from crypto_agama.agama_transform_tools import (
    ASCII_LETTERS_RE,
    convert_to_base58,
    hex_to_bin,
    hex_to_num,
    is_hex_text,
    is_valid_hex,
    num_to_bech,
    str_to_hex,
)
from lib.terminal import Terminal
from lib.wrapp_log import console_log, get_project_directory, load_config


PROJECT_ROOT = Path(__file__).resolve().parent
RESULT_LABEL_WIDTH = 8


def parse_args() -> argparse.Namespace:
    """Parse command-line options while allowing ``-status`` on its own."""

    parser = argparse.ArgumentParser(
        description="Transform project text with the XOR or ROT13 cipher.",
    )
    parser.add_argument(
        "-c",
        "--cipher",
        choices=("xor", "rot13"),
        help="Cipher to use: xor or rot13.",
    )
    parser.add_argument(
        "text",
        nargs="?",
        metavar="STRING",
        help="Text for the selected cipher. If omitted, the configured project's data.txt is used.",
    )
    parser.add_argument(
        "-s",
        "--status",
        action="store_true",
        help="Show the values loaded from y3nda_config.json.",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Try all applicable conversions on STRING or the project's data.txt.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "y3nda_config.json",
        help="Path to configuration JSON (default: %(default)s).",
    )
    return parser.parse_args()


def rot13(text: str) -> str:
    """Apply the supplied Caesar implementation without corrupting punctuation.

    ``caesar_encrypt`` handles English letters and spaces, but maps punctuation
    and non-ASCII characters into unrelated letters.  Sending only contiguous
    ASCII-letter runs to that function keeps such input intact.
    """

    return ASCII_LETTERS_RE.sub(lambda match: caesar_encrypt(match.group(), 13), text)


def read_data(data_path: Path) -> str:
    """Read the project input with an error suitable for the command line."""

    try:
        return data_path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"Cannot read data file {data_path}: {error}") from error
    except UnicodeDecodeError as error:
        raise ValueError(f"Data file is not valid UTF-8: {data_path}: {error}") from error


def get_xor_key(env_path: Path) -> str:
    """Load and validate ``XEY_HEX`` from the configured project's .env."""

    if not env_path.is_file():
        raise ValueError(f"No .env file found: {env_path}")

    key = dotenv_values(env_path).get("XEY_HEX")
    if not isinstance(key, str) or not is_valid_hex(key):
        raise ValueError(f"XEY_HEX must be a non-empty, even-length hexadecimal key in {env_path}")
    return key


def print_conversion(t: Terminal, label: str, value: object) -> None:
    """Print one green, aligned conversion label and its uncoloured value."""

    label_text = f"{label}:".ljust(RESULT_LABEL_WIDTH)
    continuation = " " * (RESULT_LABEL_WIDTH + 1)
    rendered_value = str(value).replace("\n", f"\n{continuation}")
    print(f"{t.color('g', label_text)} {rendered_value}")


def print_all_conversions(value: str, hex_key: str) -> None:
    """Print conversions appropriate to a hexadecimal value or ordinary text."""

    terminal = Terminal()
    trimmed = value.strip()
    if is_hex_text(trimmed):
        binary_text = hex_to_bin(trimmed, True)
        print_conversion(terminal, "Input", "hexadecimal")
        print_conversion(terminal, "XOR", toggle_xor(value, hex_key))
        print_conversion(terminal, "Number", hex_to_num(trimmed))
        print_conversion(terminal, "Binary", f"0b{binary_text}")
        print_conversion(terminal, "Bin str", binary_text)
        return

    text_hex = str_to_hex(value)
    text_number = int.from_bytes(value.encode("utf-8"), byteorder="big")
    print_conversion(terminal, "Input", "text")
    print_conversion(terminal, "ROT13", rot13(value))
    print_conversion(terminal, "XOR", toggle_xor(value, hex_key))
    print_conversion(terminal, "Base58", convert_to_base58(text_number))
    print_conversion(terminal, "Bech32", num_to_bech(text_number))
    print_conversion(terminal, "ASCII", text_hex)


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
        project_directory = get_project_directory(PROJECT_ROOT, config)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    with console_log(project_directory, Path(__file__).name, bool(config["log"])):
        if args.status:
            print(json.dumps(config, indent=2, ensure_ascii=False))
            print(f"Project directory: {project_directory}")
            return 0

        try:
            input_text = args.text if args.text is not None else read_data(project_directory / "data.txt")
            if args.all:
                print_all_conversions(input_text, get_xor_key(project_directory / ".env"))
                return 0
            if args.cipher is None:
                print("Error: specify -c xor or -c rot13 (or use -a/-s).", file=sys.stderr)
                return 2
            result = toggle_xor(input_text, get_xor_key(project_directory / ".env")) if args.cipher == "xor" else rot13(input_text)
        except ValueError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1

        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
