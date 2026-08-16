"""Tests for YCCT input handling that do not require a command invocation."""

import tempfile
import unittest
from pathlib import Path

from ycct import read_xor_input


class YcctTests(unittest.TestCase):
    def test_xor_reads_an_existing_hex_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "cipher.hex"
            input_path.write_text("  deadbeef\n", encoding="utf-8")

            self.assertEqual(read_xor_input(str(input_path), Path(".")), "deadbeef")

    def test_xor_keeps_nonexistent_hex_path_as_text(self):
        self.assertEqual(read_xor_input("missing.hex", Path(".")), "missing.hex")

    def test_xor_rejects_invalid_hex_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "invalid.hex"
            input_path.write_text("not hexadecimal", encoding="utf-8")

            with self.assertRaises(ValueError):
                read_xor_input(str(input_path), Path("."))


if __name__ == "__main__":
    unittest.main()
