#!/usr/bin/env python
"""Command-line interface for y3nda image/infilt tools (Yiit).

The image library is imported only when an image operation runs. This keeps
``--help`` and ``--version`` useful even before image dependencies are installed.

Requires Python 3.10 or newer. YCCT remains the Python 3.6-compatible tool.
"""

import argparse
import importlib
import sys
from pathlib import Path

from lib.wrapp_log import __version__ as WRAPP_LOG_VERSION
from lib.wrapp_log import get_project_directory, load_config


__version__ = "0.2"
MINIMUM_PYTHON = (3, 10)
CHANNELS = ("R", "G", "B")
PROJECT_ROOT = Path(__file__).resolve().parent


class YiitError(Exception):
    """An error that should be presented as a concise command-line message."""


class VersionAction(argparse.Action):
    """Print Yiit and its image-library versions."""

    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help=None):
        super().__init__(option_strings=option_strings, dest=dest, nargs=0, default=default, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        print_version()
        parser.exit()


def module_version(module_name):
    """Return a module's version without making the version command fail."""

    try:
        module = importlib.import_module(module_name)
    except ImportError as error:
        missing_name = getattr(error, "name", None) or str(error)
        return "unavailable ({0})".format(missing_name)
    return getattr(module, "__version__", "unknown")


def image_library_versions():
    """Return the versions of libraries used by Yiit."""

    return (
        ("agama_image_tools", module_version("crypto_agama.agama_image_tools")),
        ("Pillow", module_version("PIL")),
        ("numpy", module_version("numpy")),
        ("wrapp_log", WRAPP_LOG_VERSION),
    )


def print_version():
    """Print Yiit and image-library versions in the YCCT-style overview."""

    versions = image_library_versions()
    label_width = max(len(name) for name, _version in versions) + 1
    print("yiit.py {0} (Python 3.10+)".format(__version__))
    for name, version in versions:
        print("{0} {1}".format("{0}:".format(name).ljust(label_width), version))


def get_image21():
    """Load Image21 only for a command that needs image processing."""

    try:
        module = importlib.import_module("crypto_agama.agama_image_tools")
    except ImportError as error:
        raise YiitError(
            "Image operations require Pillow and numpy. Install requirements.txt first ({0}).".format(error)
        ) from error
    return module.Image21


def positive_int(value):
    """Parse an integer greater than zero for argparse."""

    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def non_negative_int(value):
    """Parse an integer greater than or equal to zero for argparse."""

    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if number < 0:
        raise argparse.ArgumentTypeError("must not be negative")
    return number


def byte_value(value):
    """Parse one RGB component."""

    number = non_negative_int(value)
    if number > 255:
        raise argparse.ArgumentTypeError("must be between 0 and 255")
    return number


def image_size(value):
    """Parse WIDTHxHEIGHT and reject zero or negative dimensions."""

    try:
        width_text, height_text = value.lower().split("x")
    except ValueError:
        raise argparse.ArgumentTypeError("must use WIDTHxHEIGHT, for example 800x600")
    return positive_int(width_text), positive_int(height_text)


def channel(value):
    """Normalize and validate one RGB channel."""

    channel_name = value.upper()
    if channel_name not in CHANNELS:
        raise argparse.ArgumentTypeError("must be one of: R, G, B")
    return channel_name


def resolve_working_path(value, project_directory):
    """Resolve a bare filename in the configured project directory.

    A path that contains a directory component stays explicit and is therefore
    interpreted relative to the current directory (or used as an absolute path).
    """

    path = Path(value)
    if path.is_absolute() or path.parent != Path("."):
        return path
    return project_directory / path


def resolve_command_paths(args, project_directory):
    """Apply configured-directory defaults to every image command path."""

    path_names = {
        "create": ("filename",),
        "crea": ("filename",),
        "copy": ("source", "destination"),
        "noise": ("filename",),
        "border": ("filename",),
        "bord": ("filename",),
        "embed": ("filename",),
        "ibin": ("filename",),
        "extract": ("filename", "output"),
        "pbin": ("filename", "output"),
        "info": ("filename",),
    }
    resolved = {}
    for name in path_names.get(args.command, ()):
        value = getattr(args, name, None)
        if value is None:
            continue
        path = resolve_working_path(value, project_directory)
        setattr(args, name, path)
        resolved[name] = path
    return resolved


def resolve_embed_source(args, project_directory):
    """Choose a hexadecimal file, ``0x`` literal, or UTF-8 text for embed."""

    if args.text:
        return args.data, "text"

    candidate = resolve_working_path(args.data, project_directory)
    if args.hex_file:
        if not candidate.is_file():
            raise YiitError("Cannot read hexadecimal input file: {0}".format(candidate))
        return candidate, "hex-file"
    if args.data.lower().startswith("0x"):
        hex_data = args.data[2:]
        if not hex_data:
            raise YiitError("Hexadecimal literal must contain at least one digit after 0x.")
        try:
            int(hex_data, 16)
        except ValueError as error:
            raise YiitError("Hexadecimal literal contains invalid data: {0}".format(args.data)) from error
        return hex_data, "hex-string"
    if candidate.is_file():
        return candidate, "hex-file"
    return args.data, "text"


def create_image(filename, size):
    """Create a new RGB image."""

    width, height = size
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    image = get_image21()(width, height)
    image.save(filename)


def copy_image(source, destination, zoom):
    """Copy an image, optionally enlarging each source pixel."""

    image_class = get_image21()
    source_image = image_class()
    source_image.load(source)
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    if zoom == 1:
        # Image21.copy uses data/temp.png for this case. Saving the loaded
        # source directly avoids that unexpected intermediate-file dependency.
        source_image.save(destination)
        return
    destination_image = image_class()
    destination_image.copy(source_image, zoom)
    destination_image.save(destination)


def add_noise(filename, channel_name, noise_range):
    """Apply a random +/- range to every pixel in one channel, in place."""

    image = get_image21()()
    image.load(filename)
    image.add_noise(channel_name, noise_range)
    image.save(filename)


def add_border(filename, thickness, color):
    """Draw a border in place."""

    image = get_image21()()
    image.load(filename)
    image.border(thickness, color)
    image.save(filename)


def embed_binary(filename, data, x, y, channel_name, source_type):
    """Embed hexadecimal-file data, a hexadecimal literal, or text in one channel."""

    if source_type == "hex-file":
        try:
            with open(data, "r", encoding="utf-8") as input_file:
                hex_data = input_file.read().strip()
        except OSError as error:
            raise YiitError("Cannot read hexadecimal input file {0}: {1}".format(data, error)) from error

        try:
            binary_data = bin(int(hex_data, 16))[2:].zfill(len(hex_data) * 4)
        except ValueError as error:
            raise YiitError("Hexadecimal input file contains invalid data: {0}".format(data)) from error
    elif source_type == "hex-string":
        binary_data = bin(int(data, 16))[2:].zfill(len(data) * 4)
    else:
        text_data = str(data)
        if not text_data:
            raise YiitError("Text data must not be empty.")
        binary_data = "".join("{0:08b}".format(byte) for byte in text_data.encode("utf-8"))

    image = get_image21()()
    image.load(filename)
    image.normalize(channel_name)

    image.infilt_bin(binary_data, x, y, channel_name)
    image.save(filename)


def extract_binary(filename, x, y, length, channel_name, verbose, output=None, output_text=None, output_hex=None):
    """Extract parity bits, optionally decode them, and optionally save them."""

    image = get_image21()()
    image.load(filename)
    binary_data = image.parse_bin(x, y, channel_name, length)
    if not binary_data:
        raise YiitError("No data can be read from the selected position.")
    hex_data = "{0:X}".format(int(binary_data, 2)).zfill((length + 3) // 4)
    print(hex_data)
    decoded_text = None
    decode_error = None
    if len(binary_data) % 8:
        decode_error = "UTF-8 decoding requires a bit length divisible by 8."
    else:
        raw_bytes = int(binary_data, 2).to_bytes(len(binary_data) // 8, byteorder="big")
        try:
            decoded_text = raw_bytes.rstrip(b"\x00").decode("utf-8")
        except UnicodeDecodeError:
            decode_error = "extracted data is not valid UTF-8 text."

    if output_text is not None and decoded_text is None:
        raise YiitError("--out-txt requires extracted data that is valid, byte-aligned UTF-8 text.")

    if output_text is not None:
        output_target = output_text
        output_data = decoded_text
        output_kind = "decoded UTF-8 text"
    elif output_hex is not None:
        output_target = output_hex
        output_data = hex_data
        output_kind = "hexadecimal data"
    elif output is not None:
        output_target = output
        if verbose and decoded_text is not None:
            output_data = decoded_text
            output_kind = "decoded UTF-8 text"
        else:
            output_data = hex_data
            output_kind = "hexadecimal data"
    else:
        output_target = None

    if output_target is not None:
        Path(output_target).parent.mkdir(parents=True, exist_ok=True)
        Path(output_target).write_text(output_data, encoding="utf-8")
        if verbose:
            print("Verbose: saved {0}: {1}".format(output_kind, output_target), file=sys.stderr)

    if not verbose:
        return
    if decode_error:
        print("Verbose: {0}".format(decode_error), file=sys.stderr)
        return
    print("Verbose: decoded UTF-8 text: {0}".format(decoded_text), file=sys.stderr)


def show_info(filename):
    """Print image dimensions, byte size, and checksums."""

    image = get_image21()()
    image.load(filename)
    image.info()


def print_examples():
    """Print current command examples without requiring image dependencies."""

    print("Examples:")
    print("  # Bare filenames use the configured yt.json subdir.")
    print("  python yiit.py -v create image.png 100x100")
    print("  python yiit.py info image.png")
    print("  python yiit.py noise image.png --channel R --range 10")
    print("  python yiit.py embed image.png data/hex.txt --x 0 --y 0 --channel R")
    print("  python yiit.py embed image.png 0x0F --x 0 --y 0 --channel R")
    print("  python yiit.py embed image.png \"text data\" --x 0 --y 0 --channel R")
    print("  python yiit.py extract image.png --x 0 --y 0 --length 128 --channel R")
    print("  python ./yiit.py embed image.png \"test 123 567\" --x 0 --y 0 --channel R")
    print("  python ./yiit.py -v extract image.png --length 128 --channel R")
    print("  python ./yiit.py -v extract image.png --length 128 --channel R --out-txt output_ascii.txt")
    print("  python ./yiit.py extract image.png --length 128 --channel R --out-hex recovered.hex")


def add_verbose_argument(parser, default):
    """Add the repeatable verbose option to the main parser or a subcommand."""

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=default,
        help="Show diagnostic output; repeat for more detail (for example: -vv).",
    )


def parse_args():
    """Create and parse the Yiit command-line interface."""

    parser = argparse.ArgumentParser(
        description="Yiit: y3nda image and parity-bit infiltration tools.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-V",
        "--ver",
        "--version",
        action=VersionAction,
        help="Show Yiit and image-library versions.",
    )
    add_verbose_argument(parser, default=0)
    parser.add_argument("-e", "--examples", action="store_true", help="Show command examples.")
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "yt.json",
        help="Path to configuration JSON (default: %(default)s).",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    create_parser = subparsers.add_parser("create", aliases=("crea",), help="Create a new RGB image.")
    add_verbose_argument(create_parser, default=argparse.SUPPRESS)
    create_parser.add_argument("filename", metavar="IMAGE", help="Output image filename.")
    create_parser.add_argument("size", metavar="WIDTHxHEIGHT", type=image_size, help="For example: 800x600.")
    create_parser.set_defaults(handler=lambda args: create_image(args.filename, args.size))

    copy_parser = subparsers.add_parser("copy", help="Copy an image, optionally enlarged.")
    add_verbose_argument(copy_parser, default=argparse.SUPPRESS)
    copy_parser.add_argument("source", metavar="SOURCE", help="Source image filename.")
    copy_parser.add_argument("destination", metavar="DESTINATION", help="Output image filename.")
    copy_parser.add_argument("-z", "--zoom", type=positive_int, default=1, help="Integer zoom factor (default: 1).")
    copy_parser.set_defaults(handler=lambda args: copy_image(args.source, args.destination, args.zoom))

    noise_parser = subparsers.add_parser("noise", help="Change every pixel in a channel, in place.")
    add_verbose_argument(noise_parser, default=argparse.SUPPRESS)
    noise_parser.add_argument("filename", metavar="IMAGE", help="Image filename to modify.")
    noise_parser.add_argument("-c", "--channel", type=channel, default="R", help="RGB channel (default: R).")
    noise_parser.add_argument(
        "-r", "--range", "-f", "--fill", dest="noise_range", type=non_negative_int, default=10,
        help="Maximum random +/- change per pixel (default: 10).",
    )
    noise_parser.set_defaults(handler=lambda args: add_noise(args.filename, args.channel, args.noise_range))

    border_parser = subparsers.add_parser("border", aliases=("bord",), help="Add a border in place.")
    add_verbose_argument(border_parser, default=argparse.SUPPRESS)
    border_parser.add_argument("filename", metavar="IMAGE", help="Image filename to modify.")
    border_parser.add_argument("-t", "--thickness", type=non_negative_int, default=2, help="Border width (default: 2).")
    border_parser.add_argument(
        "-c", "--color", nargs=3, type=byte_value, default=(128, 128, 128), metavar=("R", "G", "B"),
        help="Border colour as R G B (default: 128 128 128).",
    )
    border_parser.set_defaults(handler=lambda args: add_border(args.filename, args.thickness, tuple(args.color)))

    embed_parser = subparsers.add_parser(
        "embed", aliases=("ibin",), help="Embed hexadecimal-file data or literal text in one RGB channel, in place."
    )
    add_verbose_argument(embed_parser, default=argparse.SUPPRESS)
    embed_parser.add_argument("filename", metavar="IMAGE", help="Image filename to modify.")
    embed_parser.add_argument(
        "data",
        metavar="HEX_FILE_OR_TEXT",
        help="Existing hex file, 0x-prefixed hexadecimal literal, or UTF-8 text to embed.",
    )
    source_group = embed_parser.add_mutually_exclusive_group()
    source_group.add_argument("--text", action="store_true", help="Always treat HEX_FILE_OR_TEXT as literal UTF-8 text.")
    source_group.add_argument("--hex-file", action="store_true", help="Require HEX_FILE_OR_TEXT to be a hexadecimal input file.")
    embed_parser.add_argument("-x", "--x", type=non_negative_int, default=0, help="Starting X coordinate (default: 0).")
    embed_parser.add_argument("-y", "--y", type=non_negative_int, default=0, help="Starting Y coordinate (default: 0).")
    embed_parser.add_argument("-c", "--channel", type=channel, default="R", help="RGB channel (default: R).")
    embed_parser.set_defaults(
        handler=lambda args: embed_binary(
            args.filename, args.data, args.x, args.y, args.channel, args.embed_source_type
        )
    )

    extract_parser = subparsers.add_parser(
        "extract", aliases=("pbin",), help="Extract parity bits from one RGB channel as hexadecimal data."
    )
    add_verbose_argument(extract_parser, default=argparse.SUPPRESS)
    extract_parser.add_argument("filename", metavar="IMAGE", help="Image filename to read.")
    extract_parser.add_argument("-x", "--x", type=non_negative_int, default=0, help="Starting X coordinate (default: 0).")
    extract_parser.add_argument("-y", "--y", type=non_negative_int, default=0, help="Starting Y coordinate (default: 0).")
    extract_parser.add_argument("-l", "--length", type=positive_int, default=32, help="Number of bits to read (default: 32).")
    extract_parser.add_argument("-c", "--channel", type=channel, default="R", help="RGB channel (default: R).")
    output_group = extract_parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--out-txt",
        dest="output_text",
        metavar="FILE",
        help="Save decoded UTF-8 text; fails when the extracted data is not UTF-8 text.",
    )
    output_group.add_argument(
        "--out-hex",
        dest="output_hex",
        metavar="FILE",
        help="Save extracted data as hexadecimal text, suitable for embed.",
    )
    output_group.add_argument(
        "--out",
        dest="output",
        metavar="FILE",
        help="Legacy automatic output: hexadecimal, or decoded UTF-8 text with -v.",
    )
    extract_parser.set_defaults(
        handler=lambda args: extract_binary(
            args.filename,
            args.x,
            args.y,
            args.length,
            args.channel,
            args.verbose,
            args.output,
            args.output_text,
            args.output_hex,
        )
    )

    info_parser = subparsers.add_parser("info", help="Show image size and checksums.")
    add_verbose_argument(info_parser, default=argparse.SUPPRESS)
    info_parser.add_argument("filename", metavar="IMAGE", help="Image filename to inspect.")
    info_parser.set_defaults(handler=lambda args: show_info(args.filename))

    lib_parser = subparsers.add_parser("lib", help="Show Yiit and image-library versions (same as --version).")
    add_verbose_argument(lib_parser, default=argparse.SUPPRESS)
    lib_parser.set_defaults(handler=lambda args: print_version())

    return parser, parser.parse_args()


def main():
    """Run Yiit and render expected command errors without a traceback."""

    if sys.version_info < MINIMUM_PYTHON:
        print("Error: yiit.py requires Python 3.10 or newer.", file=sys.stderr)
        return 1

    parser, args = parse_args()
    if args.verbose:
        print("Verbose: yiit.py {0} invoked.".format(__version__), file=sys.stderr)
        if args.command:
            print("Verbose: command: {0}.".format(args.command), file=sys.stderr)
        if args.verbose >= 2 and args.command:
            options = {
                key: value for key, value in vars(args).items()
                if key not in ("handler", "verbose", "command")
            }
            print("Verbose: options: {0}".format(options), file=sys.stderr)
    if args.examples:
        print_examples()
        return 0
    if not hasattr(args, "handler"):
        parser.print_help()
        return 2
    if args.command == "lib":
        args.handler(args)
        return 0

    try:
        config = load_config(args.config)
        project_directory = get_project_directory(PROJECT_ROOT, config)
        resolved_paths = resolve_command_paths(args, project_directory)
        if args.command in ("embed", "ibin"):
            args.data, args.embed_source_type = resolve_embed_source(args, project_directory)
            if args.embed_source_type == "hex-file":
                resolved_paths["data"] = args.data
            elif args.embed_source_type == "hex-string":
                resolved_paths["data"] = "<literal hexadecimal>"
            else:
                resolved_paths["data"] = "<literal UTF-8 text>"
    except (ValueError, YiitError) as error:
        print("Error: {0}".format(error), file=sys.stderr)
        return 1

    if args.verbose:
        print("Verbose: configuration file: {0}".format(args.config), file=sys.stderr)
        print("Verbose: project directory: {0}".format(project_directory), file=sys.stderr)
    if args.verbose >= 2 and resolved_paths:
        rendered_paths = ", ".join(
            "{0}={1}".format(name, path) for name, path in sorted(resolved_paths.items())
        )
        print("Verbose: resolved paths: {0}".format(rendered_paths), file=sys.stderr)

    try:
        args.handler(args)
    except (OSError, ValueError, YiitError) as error:
        print("Error: {0}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
