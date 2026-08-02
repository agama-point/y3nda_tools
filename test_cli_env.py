"""Tests for the Python 3.6-compatible .env command-line interface."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import cli_env


class CliEnvTests(unittest.TestCase):
    def test_short_option_aliases_are_parsed(self):
        with patch.object(sys, "argv", ["cli_env.py", "-c", "custom.json", "-e", "other.env", "-l", "--no-log"]):
            args = cli_env.parse_args()

        self.assertEqual(str(args.config), "custom.json")
        self.assertEqual(str(args.env_file), "other.env")
        self.assertTrue(args.load)
        self.assertTrue(args.no_log)

    def test_print_values_can_hide_values(self):
        with patch("sys.stdout") as output:
            result = cli_env.print_values({"TOKEN": "secret", "EMPTY": None}, names_only=True)

        self.assertEqual(result, 0)
        output.write.assert_any_call("  TOKEN")
        self.assertFalse(any("secret" in str(call) for call in output.write.call_args_list))

    def test_print_values_reports_unknown_key(self):
        with patch("sys.stderr") as output:
            result = cli_env.print_values({"TOKEN": "secret"}, key="MISSING")

        self.assertEqual(result, 1)
        output.write.assert_any_call("No value named 'MISSING' in the .env file.")

    def test_fallback_dotenv_reader_handles_simple_entries(self):
        env_path = Path(__file__).with_name("project_test") / ".env"
        values = cli_env._fallback_dotenv_values(env_path)

        self.assertIn("XEY_HEX", values)
        self.assertTrue(values["XEY_HEX"])

    @patch("cli_env.WRAPP_LOG_AVAILABLE", False)
    def test_missing_optional_log_wrapper_uses_current_directory(self):
        with patch("sys.stderr") as output:
            project_directory, logging_enabled = cli_env.get_project_settings(Path("missing.json"))

        self.assertEqual(project_directory, Path.cwd().resolve())
        self.assertFalse(logging_enabled)
        self.assertIn("optional lib.wrapp_log is unavailable", str(output.write.call_args_list))


if __name__ == "__main__":
    unittest.main()
