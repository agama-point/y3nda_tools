"""Bidirectional lookups for the project mnemonic word lists.

All indexes are zero-based: ``bip(0)`` is ``"abandon"`` and
``bip("abandon")`` is ``0``.  This matches the BIP-0039 and SLIP-0039
specifications and makes CIP's first word, ``amber``, index 0 as well.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final


_ASSETS_DIR: Final = Path(__file__).with_name("assets")


def _load_word_list(filename: str, expected_length: int) -> tuple[str, ...]:
    """Load and validate a whitespace-delimited word list shipped with this package."""
    words = tuple((_ASSETS_DIR / filename).read_text(encoding="utf-8").split())
    if len(words) != expected_length or len(set(words)) != expected_length:
        raise RuntimeError(f"Invalid mnemonic word list: {filename}")
    return words


_CIP_WORDS: Final = _load_word_list("cip.txt", 16)
_BIP_WORDS: Final = _load_word_list("bip.txt", 2048)
_SLIP_WORDS: Final = _load_word_list("slip.txt", 1024)
MNEMONIC_WORD_COLUMN_WIDTH: Final = max(
    len(word) for word_list in (_CIP_WORDS, _BIP_WORDS, _SLIP_WORDS) for word in word_list
) + 2


def _lookup(value: int | str, words: tuple[str, ...]) -> str | int:
    """Return a word for a zero-based index, or its zero-based index for a word."""
    if isinstance(value, bool):
        raise TypeError("Mnemonic lookup accepts an integer index or a word string, not bool")
    if isinstance(value, int):
        if not 0 <= value < len(words):
            raise IndexError(f"Mnemonic index must be from 0 to {len(words) - 1}")
        return words[value]
    if isinstance(value, str):
        word = value.strip().lower()
        try:
            return words.index(word)
        except ValueError as error:
            raise ValueError(f"Unknown mnemonic word: {value!r}") from error
    raise TypeError("Mnemonic lookup accepts an integer index or a word string")


def cip(value: int | str) -> str | int:
    """Look up a CIP word or its zero-based index (valid indexes: 0--15)."""
    return _lookup(value, _CIP_WORDS)


def bip(value: int | str) -> str | int:
    """Look up a BIP-0039 word or its zero-based index (valid indexes: 0--2047)."""
    return _lookup(value, _BIP_WORDS)


def slip(value: int | str) -> str | int:
    """Look up a SLIP-0039 word or its zero-based index (valid indexes: 0--1023)."""
    return _lookup(value, _SLIP_WORDS)
