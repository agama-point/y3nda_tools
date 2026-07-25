"""Simple progress bar using lib.wrapp_terminal.status_line."""

import time

from lib.wrapp_terminal import progress_bar, status_line


def main() -> None:
    total = 100

    for current in range(total + 1):
        status_line(progress_bar(current, total))
        time.sleep(0.05)

    print("\nDone.")


if __name__ == "__main__":
    main()
