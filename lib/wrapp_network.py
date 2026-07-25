"""Small, dependency-free helpers for basic local network diagnostics."""

import os
import socket
import subprocess
from urllib.error import URLError
from urllib.request import Request, urlopen

from lib.wrapp_terminal import Terminal


__version__ = "0.26.01"


DEFAULT_PING_HOST = "8.8.8.8"
INTERNET_CHECK_URL = "https://example.com/"


def get_local_ipv4() -> str:
    """Return the IPv4 address selected by the default route, or ``unavailable``."""

    connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        connection.connect((DEFAULT_PING_HOST, 53))
        return connection.getsockname()[0]
    except OSError:
        return "unavailable"
    finally:
        connection.close()


def ping_once(host: str = DEFAULT_PING_HOST) -> bool:
    """Return whether one operating-system ping to ``host`` succeeds."""

    if os.name == "nt":
        command = ("ping", "-n", "1", "-w", "1000", host)
    else:
        command = ("ping", "-c", "1", "-W", "1", host)

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def check_internet(url: str = INTERNET_CHECK_URL) -> bool:
    """Return whether an HTTPS request to a public site succeeds."""

    request = Request(url, headers={"User-Agent": "y3nda-network-check/1.0"})
    try:
        with urlopen(request, timeout=5) as response:
            return 200 <= response.getcode() < 400
    except (OSError, URLError, ValueError):
        return False


def print_network_info() -> None:
    """Print local IPv4, an HTTPS internet check, and one ICMP ping result."""

    terminal = Terminal()
    print(terminal.color("g", "Network information"))
    print("Local IPv4: {0}".format(get_local_ipv4()))
    internet_available = check_internet()
    internet_state = "available" if internet_available else "unavailable"
    internet_color = "g" if internet_available else "r"
    print("Internet (HTTPS): {0}".format(terminal.color(internet_color, internet_state)))
    reachable = ping_once(DEFAULT_PING_HOST)
    ping_state = "reply received" if reachable else "no ICMP reply"
    ping_color = "g" if reachable else "y"
    print("Ping {0} (ICMP): {1}".format(DEFAULT_PING_HOST, terminal.color(ping_color, ping_state)))
