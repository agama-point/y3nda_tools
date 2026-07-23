"""Portable, dependency-free terminal colors for small command-line tools."""

from __future__ import annotations

import os
import sys
from typing import TextIO

RESET = "\033[0m"
COLORS = {
    "r": "\033[31m",  # red
    "g": "\033[32m",  # green
    "b": "\033[34m",  # blue
    "y": "\033[93m",  # bright yellow, usually perceived as orange
    "w": "\033[97m",  # bright white
}


def _enable_windows_ansi(stream: TextIO) -> bool:
    """Enable ANSI output on supported Windows consoles without dependencies."""

    if os.name != "nt":
        return True

    try:
        import ctypes
        import msvcrt

        handle = msvcrt.get_osfhandle(stream.fileno())
        mode = ctypes.c_uint()
        kernel32 = ctypes.windll.kernel32
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))
    except (AttributeError, OSError):
        return False


def colors_enabled(stream: TextIO | None = None) -> bool:
    """Return whether ANSI colors should be used for the selected stream."""

    output = stream or sys.stdout
    if os.environ.get("NO_COLOR") or not output.isatty():
        return False
    return _enable_windows_ansi(output)


def color_text(text: object, color: str, *, enabled: bool | None = None) -> str:
    """Return text in the requested color, or plain text when colors are disabled."""

    if color not in COLORS:
        raise ValueError(f"Unknown terminal color: {color}")
    use_colors = colors_enabled() if enabled is None else enabled
    value = str(text)
    return f"{COLORS[color]}{value}{RESET}" if use_colors else value


class Terminal:
    """Print colored terminal text through short color methods."""

    def __init__(self, file: TextIO | None = None) -> None:
        self._file = file

    def print(
        self,
        color: str,
        *values: object,
        sep: str = " ",
        end: str = "\n",
    ) -> None:
        """Print values in one of the r, g, b, y, or w terminal colors."""

        output = self._file or sys.stdout
        text = sep.join(str(value) for value in values)
        print(color_text(text, color, enabled=colors_enabled(output)), end=end, file=output)

    def color(self, color: str, text: object) -> str:
        """Return one piece of text in color for use inside a longer line."""

        output = self._file or sys.stdout
        return color_text(text, color, enabled=colors_enabled(output))

    def r(self, *values: object, **kwargs: object) -> None:
        """Print in red."""

        self.print("r", *values, **kwargs)

    def g(self, *values: object, **kwargs: object) -> None:
        """Print in green."""

        self.print("g", *values, **kwargs)

    def b(self, *values: object, **kwargs: object) -> None:
        """Print in blue."""

        self.print("b", *values, **kwargs)

    def y(self, *values: object, **kwargs: object) -> None:
        """Print in bright yellow/orange."""

        self.print("y", *values, **kwargs)

    def w(self, *values: object, **kwargs: object) -> None:
        """Print in white."""

        self.print("w", *values, **kwargs)


def r(*values: object, **kwargs: object) -> None:
    """Print in red."""

    Terminal().r(*values, **kwargs)


def g(*values: object, **kwargs: object) -> None:
    """Print in green."""

    Terminal().g(*values, **kwargs)


def b(*values: object, **kwargs: object) -> None:
    """Print in blue."""

    Terminal().b(*values, **kwargs)


def y(*values: object, **kwargs: object) -> None:
    """Print in bright yellow/orange."""

    Terminal().y(*values, **kwargs)


def w(*values: object, **kwargs: object) -> None:
    """Print in white."""

    Terminal().w(*values, **kwargs)


def t100(*values: object, **kwargs: object) -> None:
    """Backward-compatible name for green output; prefer ``g(...)``."""

    g(*values, **kwargs)
