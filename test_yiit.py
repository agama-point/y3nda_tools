"""Tests for Yiit's input-source selection without image dependencies."""

import unittest
from pathlib import Path
from types import SimpleNamespace

from yiit import YiitError, resolve_embed_source


class YiitTests(unittest.TestCase):
    def test_embed_accepts_prefixed_hexadecimal_literal(self):
        args = SimpleNamespace(data="0xABC", text=False, hex_file=False)

        data, source_type = resolve_embed_source(args, Path("."))

        self.assertEqual(data, "ABC")
        self.assertEqual(source_type, "hex-string")

    def test_embed_rejects_invalid_prefixed_hexadecimal_literal(self):
        args = SimpleNamespace(data="0xABG", text=False, hex_file=False)

        with self.assertRaises(YiitError):
            resolve_embed_source(args, Path("."))

    def test_text_flag_overrides_hexadecimal_literal_detection(self):
        args = SimpleNamespace(data="0xABC", text=True, hex_file=False)

        data, source_type = resolve_embed_source(args, Path("."))

        self.assertEqual(data, "0xABC")
        self.assertEqual(source_type, "text")


if __name__ == "__main__":
    unittest.main()
