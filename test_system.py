"""Tests for the local system-information wrapper."""

import io
import unittest
from pathlib import Path
from unittest.mock import patch

from lib.wrapp_system import format_bytes, get_operating_system, get_system_info, print_system_info


class SystemTests(unittest.TestCase):
    def test_format_bytes_uses_binary_units(self):
        self.assertEqual(format_bytes(1023), "1023 B")
        self.assertEqual(format_bytes(1024), "1.0 KiB")
        self.assertEqual(format_bytes(3 * 1024 ** 3), "3.0 GiB")

    @patch("lib.wrapp_system.platform.win32_ver", return_value=("10", "10.0.22631", "", ""))
    @patch("lib.wrapp_system.platform.system", return_value="Windows")
    def test_operating_system_detects_windows_11_builds(self, _system, _win32_ver):
        self.assertEqual(get_operating_system(), "Windows 11 (10.0.22631)")

    @patch("lib.wrapp_system.get_disk_info")
    @patch("lib.wrapp_system.get_total_memory_bytes", return_value=8 * 1024 ** 3)
    @patch("lib.wrapp_system.get_python_version", return_value="CPython 3.6.15")
    @patch("lib.wrapp_system.get_operating_system", return_value="Linux - Ubuntu 24.04 LTS (GNOME)")
    @patch("lib.wrapp_system.get_computer_description", return_value="x86_64, 8 CPU threads")
    @patch("lib.wrapp_system.get_computer_name", return_value="workstation")
    def test_get_system_info_returns_concise_labels(
        self, _computer_name, _description, _system, _python, _memory, disk_info
    ):
        disk_info.return_value = {
            "path": "/",
            "total_bytes": 100 * 1024 ** 3,
            "free_bytes": 25 * 1024 ** 3,
        }

        details = get_system_info(Path("."))

        self.assertEqual(details["computer"], "workstation (x86_64, 8 CPU threads)")
        self.assertEqual(details["operating_system"], "Linux - Ubuntu 24.04 LTS (GNOME)")
        self.assertEqual(details["python"], "CPython 3.6.15")
        self.assertEqual(details["memory"], "8.0 GiB")
        self.assertEqual(details["disk"], "/: 100.0 GiB total, 25.0 GiB free (25 %)")

    @patch("lib.wrapp_system.get_system_info")
    def test_print_system_info_is_structured(self, system_info):
        system_info.return_value = {
            "computer": "workstation (x86_64)",
            "operating_system": "Linux - Ubuntu",
            "python": "CPython 3.6.15",
            "memory": "8.0 GiB",
            "disk": "/: 100.0 GiB total, 25.0 GiB free (25 %)",
        }
        output = io.StringIO()
        with patch("sys.stdout", output):
            print_system_info()

        rendered = output.getvalue()
        self.assertIn("System information", rendered)
        self.assertIn("Computer:", rendered)
        self.assertIn("Operating system:", rendered)
        self.assertIn("Python:", rendered)
        self.assertIn("Memory:", rendered)
        self.assertIn("Disk:", rendered)


if __name__ == "__main__":
    unittest.main()
