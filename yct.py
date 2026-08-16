#!/usr/bin/env python
"""Main command-line entry point for the small y3nda code/cipher project.

The command reads the project subdirectory from ``yt.json`` and
prints the transformed value.  It deliberately does not overwrite
``data.txt``: redirect its output or copy the result there only when that is
really intended.

Compatible with Python 3.6 and newer.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from crypto_agama.agama_cipher import __version__ as AGAMA_CIPHER_VERSION
from crypto_agama.agama_cipher import caesar_encrypt, p1, polybius_decrypt, toggle_xor
from crypto_agama.agama_mnemonic import __version__ as AGAMA_MNEMONIC_VERSION
from crypto_agama.agama_mnemonic import MNEMONIC_WORD_COLUMN_WIDTH, bip, cip, slip
from crypto_agama.agama_transform_tools import (
    ASCII_LETTERS_RE,
    convert_to_base58,
    hex_to_bin,
    hex_to_num,
    is_hex_text,
    is_valid_hex,
    hexdump,
    num_to_bech,
    num_to_dice,
    num_to_hex,
    str_to_hex,
    to_leet_speak,
)
from crypto_agama.agama_transform_tools import __version__ as AGAMA_TRANSFORM_TOOLS_VERSION
from lib.wrapp_terminal import Terminal
from lib.wrapp_terminal import __version__ as WRAPP_TERMINAL_VERSION
from lib.wrapp_network import print_network_info
from lib.wrapp_network import __version__ as WRAPP_NETWORK_VERSION
from lib.wrapp_system import print_system_info
from lib.wrapp_system import __version__ as WRAPP_SYSTEM_VERSION
from lib.wrapp_log import console_log, get_project_directory, load_config
from lib.wrapp_log import __version__ as WRAPP_LOG_VERSION
from lib.wrapp_run import FlowError, FlowRunner
from lib.wrapp_run import __version__ as WRAPP_RUN_VERSION


PROJECT_ROOT = Path(__file__).resolve().parent
__version__ = "0.3"
RESULT_LABEL_WIDTH = 8
POLYBIUS_TEXT_RE = re.compile(r"^[A-Za-z]+$")
POLYBIUS_NUMBERS_RE = re.compile(r"^[1-5]{2}(?:\s+[1-5]{2})*$")
POLYBIUS_LETTERS = {coordinates: letter for letter, coordinates in p1.items()}
MODULE_VERSIONS = (
    ("agama_transform_tools", AGAMA_TRANSFORM_TOOLS_VERSION),
    ("agama_mnemonic", AGAMA_MNEMONIC_VERSION),
    ("agama_cipher", AGAMA_CIPHER_VERSION),
    ("wrapp_log", WRAPP_LOG_VERSION),
    ("wrapp_run", WRAPP_RUN_VERSION),
    ("wrapp_terminal", WRAPP_TERMINAL_VERSION),
    ("wrapp_network", WRAPP_NETWORK_VERSION),
    ("wrapp_system", WRAPP_SYSTEM_VERSION),
)
VERSION_LABEL_WIDTH = max(len(name) for name, _version in MODULE_VERSIONS) + 1


class VersionAction(argparse.Action):
    """Print a colorized, aligned version overview."""

    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help=None):
        super().__init__(option_strings=option_strings, dest=dest, nargs=0, default=default, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        terminal = Terminal()
        print(terminal.color("y", "yct.py {0} (Python 3.6+)".format(__version__)))
        for name, version in MODULE_VERSIONS:
            label = "{0}:".format(name).ljust(VERSION_LABEL_WIDTH)
            print("{0} {1}".format(terminal.color("g", label), version))
        parser.exit()


def parse_args() -> argparse.Namespace:
    """Parse command-line options while allowing ``-status`` on its own."""

    parser = argparse.ArgumentParser(
        description="Transform project text with the XOR, ROT13, Polybius, or leet cipher.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-V",
        "-v",
        "--ver",
        "--version",
        action=VersionAction,
        help="Show yct.py and submodule versions.",
    )
    parser.add_argument(
        "-c",
        "--cipher",
        "--code",
        choices=("xor", "rot13", "polybius", "leet"),
        help="Cipher to use: xor, rot13, polybius, or leet.",
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
        help="Show project configuration and local system information.",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Try all applicable conversions on STRING or the project's data.txt.",
    )
    parser.add_argument(
        "-d",
        "--dump",
        action="store_true",
        help="Hexdump the configured working directory's data.txt.",
    )
    parser.add_argument(
        "-m",
        "--mnemonic",
        metavar="STRING",
        help="Look up a CIP, SLIP-0039, or BIP-0039 mnemonic word or zero-based index.",
    )
    parser.add_argument(
        "-n",
        "--net",
        action="store_true",
        help="Show local IPv4, HTTPS internet access, and one ping to 8.8.8.8.",
    )
    parser.add_argument(
        "-r",
        "--run",
        nargs="?",
        const=Path("flow.txt"),
        metavar="FILE",
        type=Path,
        help="Run FILE, or flow.txt by default, from the root or configured working directory.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "yt.json",
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


def polybius_transform(value: str) -> str:
    """Encode letters or decode space-separated Polybius coordinates.

    Text input such as ``agama`` is encoded through ``polybius_decrypt``.
    Coordinates such as ``11 22 11 32 11`` are decoded to uppercase text.
    """

    value = value.strip()
    if POLYBIUS_NUMBERS_RE.fullmatch(value):
        return "".join(POLYBIUS_LETTERS[coordinate] for coordinate in value.split())
    if POLYBIUS_TEXT_RE.fullmatch(value):
        return polybius_decrypt(value)
    raise ValueError(
        "Polybius input must be letters, or two-digit coordinates 11–55 separated by spaces."
    )


def leet_transform(value: str) -> str:
    """Convert text with the full leetspeak mapping."""

    return to_leet_speak(value, 2)


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

    try:
        from dotenv import dotenv_values
    except ImportError as error:
        raise ValueError("XOR operations require the python-dotenv package") from error

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
        # print_conversion(terminal, "Binary", f"0b{binary_text}")
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


def print_mnemonic_lookup(value: str) -> None:
    """Print mnemonic matches for a word or a non-negative decimal index.

    Word matches show a zero-based index and its fixed-width binary encoding:
    4 bits for CIP, 10 for SLIP-0039, and 11 for BIP-0039.  Numeric input
    shows the corresponding word, or ``-`` when that index is unavailable.
    """

    lookups = (("CIP", cip, 4), ("SLIP", slip, 10), ("BIP", bip, 11))
    numeric_match = re.fullmatch(r"[+-]?\d+", value.strip())
    lookup_value = int(value) if numeric_match else value
    terminal = Terminal()

    for label, lookup, bit_width in lookups:
        try:
            result = lookup(lookup_value)
        except (IndexError, ValueError):
            result = "-"
        else:
            if isinstance(lookup_value, str):
                result = f"{result}  {terminal.color('y', f'{result:0{bit_width}b}')}"
            else:
                result = f"{result:<{MNEMONIC_WORD_COLUMN_WIDTH}}{terminal.color('y', f'{lookup_value:0{bit_width}b}')}"
        print_conversion(terminal, label, result)

    if isinstance(lookup_value, int):
        if lookup_value < 0:
            print_conversion(terminal, "HEX", "-")
            print_conversion(terminal, "BECH32", "-")
            print_conversion(terminal, "DICE", "-")
        else:
            print_conversion(terminal, "HEX", num_to_hex(lookup_value)[2:])
            print_conversion(terminal, "BECH32", num_to_bech(lookup_value).upper())
            print_conversion(terminal, "DICE", num_to_dice(lookup_value, 5))


def main() -> int:
    if len(sys.argv) == 1:
        print("Info: use -h for help.")
        return 0

    args = parse_args()
    if args.mnemonic is not None:
        print_mnemonic_lookup(args.mnemonic)
        return 0
    if args.net:
        print_network_info()
        return 0

    try:
        config = load_config(args.config)
        project_directory = get_project_directory(PROJECT_ROOT, config)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    with console_log(project_directory, Path(__file__).name, bool(config["log"])):
        if args.status:
            terminal = Terminal()
            print(terminal.color("y", "Project status"))
            print("{0} {1}".format(terminal.color("g", "Configuration:"), json.dumps(config, ensure_ascii=False)))
            print("{0} {1}".format(terminal.color("g", "Project directory:"), project_directory))
            print()
            print_system_info(project_directory)
            return 0

        try:
            if args.run is not None:
                flow_runner = FlowRunner(PROJECT_ROOT, flow_directories=(project_directory,))
                flow_path = flow_runner.resolve_flow_path(args.run)
                return flow_runner.run(flow_path, flow_runner.load(flow_path))
            if args.dump:
                try:
                    data = (project_directory / "data.txt").read_bytes()
                except OSError as error:
                    raise ValueError(f"Cannot read data file {project_directory / 'data.txt'}: {error}") from error
                hexdump(data)
                return 0
            input_text = args.text if args.text is not None else read_data(project_directory / "data.txt")
            if args.all:
                print_all_conversions(input_text, get_xor_key(project_directory / ".env"))
                return 0
            if args.cipher is None:
                print("Error: specify -c xor, -c rot13, -c polybius, or -c leet (or use -a/-s).", file=sys.stderr)
                return 2
            if args.cipher == "xor":
                result = toggle_xor(input_text, get_xor_key(project_directory / ".env"))
            elif args.cipher == "rot13":
                result = rot13(input_text)
            elif args.cipher == "polybius":
                result = polybius_transform(input_text)
            else:
                result = leet_transform(input_text)
        except (FlowError, ValueError) as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1

        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
