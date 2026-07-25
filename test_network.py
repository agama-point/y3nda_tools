"""Tests for the basic network diagnostics helpers."""

import io
import subprocess
import unittest
from urllib.error import URLError
from unittest.mock import MagicMock, Mock, patch

from lib.wrapp_network import check_internet, get_local_ipv4, ping_once, print_network_info


class NetworkTests(unittest.TestCase):
    def test_get_local_ipv4_uses_default_route(self):
        connection = Mock()
        connection.getsockname.return_value = ("192.168.1.50", 0)
        with patch("lib.wrapp_network.socket.socket", return_value=connection):
            self.assertEqual(get_local_ipv4(), "192.168.1.50")

        connection.connect.assert_called_once_with(("8.8.8.8", 53))
        connection.close.assert_called_once_with()

    def test_ping_once_uses_one_windows_ping(self):
        completed = Mock(returncode=0)
        with patch("lib.wrapp_network.os.name", "nt"), patch(
            "lib.wrapp_network.subprocess.run", return_value=completed
        ) as run:
            self.assertTrue(ping_once())

        run.assert_called_once_with(
            ("ping", "-n", "1", "-w", "1000", "8.8.8.8"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
            check=False,
        )

    def test_ping_once_returns_false_when_ping_is_unavailable(self):
        with patch("lib.wrapp_network.subprocess.run", side_effect=OSError):
            self.assertFalse(ping_once())

    def test_check_internet_accepts_successful_https_response(self):
        response = MagicMock()
        response.getcode.return_value = 200
        response.__enter__.return_value = response
        with patch("lib.wrapp_network.urlopen", return_value=response) as open_url:
            self.assertTrue(check_internet())

        arguments, keyword_arguments = open_url.call_args
        self.assertEqual(arguments[0].full_url, "https://example.com/")
        self.assertEqual(keyword_arguments["timeout"], 5)

    def test_check_internet_returns_false_for_connection_error(self):
        with patch("lib.wrapp_network.urlopen", side_effect=URLError("offline")):
            self.assertFalse(check_internet())

    def test_print_network_info_shows_ip_and_ping_result(self):
        output = io.StringIO()
        with patch("lib.wrapp_network.get_local_ipv4", return_value="192.168.1.50"), patch(
            "lib.wrapp_network.ping_once", return_value=True
        ), patch(
            "lib.wrapp_network.check_internet", return_value=True
        ), patch("sys.stdout", output):
            print_network_info()

        rendered = output.getvalue()
        self.assertIn("Local IPv4: 192.168.1.50", rendered)
        self.assertIn("Internet (HTTPS): available", rendered)
        self.assertIn("Ping 8.8.8.8 (ICMP): reply received", rendered)


if __name__ == "__main__":
    unittest.main()
