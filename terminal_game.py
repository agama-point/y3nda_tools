"""A small terminal game: collect every green symbol.

Run in a Windows terminal with::

    python terminal_game.py
"""

import json
import msvcrt
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple

from lib.wrapp_terminal import Terminal, ansi_enabled, clear_line, cursor_up


Point = Tuple[int, int]
CONFIG_PATH = Path(__file__).with_name("terminal_game.json")

ARROW_KEYS = {
    "H": (0, -1),  # Up
    "P": (0, 1),   # Down
    "K": (-1, 0),  # Left
    "M": (1, 0),   # Right
}


class GameConfig(object):
    """Validated settings loaded from the configuration file."""

    def __init__(self, width, height, snake, dot_count, dot_symbol):
        self.width = width
        self.height = height
        self.snake = snake
        self.dot_count = dot_count
        self.dot_symbol = dot_symbol


def load_config(path=CONFIG_PATH):
    """Load and validate game settings from a JSON file."""

    try:
        values = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError("Could not read configuration {0}: {1}".format(path, error))
    except json.JSONDecodeError as error:
        raise ValueError("Configuration {0} is not valid JSON: {1}".format(path, error.msg))

    if not isinstance(values, dict):
        raise ValueError("Configuration must be a JSON object.")

    dimensions = {}  # type: Dict[str, int]
    for key in ("width", "height", "dot_count"):
        value = values.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError("Setting {0!r} must be a positive integer.".format(key))
        dimensions[key] = value

    snake = values.get("snake")
    if not isinstance(snake, bool):
        raise ValueError("Setting 'snake' must be true or false.")

    dot_symbol = values.get("dot_symbol")
    if not isinstance(dot_symbol, str) or len(dot_symbol) != 1:
        raise ValueError("Setting 'dot_symbol' must contain exactly one character.")

    if dimensions["width"] * dimensions["height"] <= dimensions["dot_count"]:
        raise ValueError("The board must have more cells than the dot count.")
    return GameConfig(
        dimensions["width"],
        dimensions["height"],
        snake,
        dimensions["dot_count"],
        dot_symbol,
    )


class Game(object):
    """Game state and movement rules for the bordered board."""

    def __init__(self, width, height, player, snake, dot_count, dot_symbol, dots, snake_body):
        self.width = width
        self.height = height
        self.player = player
        self.snake = snake
        self.dot_count = dot_count
        self.dot_symbol = dot_symbol
        self.dots = dots
        self.snake_body = snake_body
        self.score = 0

    @classmethod
    def new(cls, config):
        """Create a new game with dots away from the player's starting cell."""

        player = (config.width // 2, config.height // 2)
        available = [
            (x, y)
            for y in range(config.height)
            for x in range(config.width)
            if (x, y) != player
        ]
        return cls(
            config.width,
            config.height,
            player,
            config.snake,
            config.dot_count,
            config.dot_symbol,
            set(random.sample(available, config.dot_count)),
            [player],
        )

    def move(self, dx, dy):
        """Move the player when the target is inside the board and not the snake."""

        x, y = self.player
        target = (x + dx, y + dy)
        target_x, target_y = target
        if not (0 <= target_x < self.width and 0 <= target_y < self.height):
            return False

        eats_dot = target in self.dots
        if self.snake:
            occupied_body = self.snake_body if eats_dot else self.snake_body[:-1]
            if target in occupied_body:
                return False
            self.snake_body.insert(0, target)
            if not eats_dot:
                self.snake_body.pop()

        self.player = target
        if eats_dot:
            self.dots.remove(target)
            self.score += 1
        return True


def read_direction():
    """Read an arrow without blocking; return None when Q is pressed."""

    if not msvcrt.kbhit():
        return ()
    key = msvcrt.getwch()
    if key.lower() == "q":
        return None
    if key not in ("\x00", "\xe0"):
        return ()
    return ARROW_KEYS.get(msvcrt.getwch(), ())


def format_time(elapsed_seconds):
    """Format elapsed seconds as minutes and seconds."""

    minutes, seconds = divmod(elapsed_seconds, 60)
    return "{0:02d}:{1:02d}".format(minutes, seconds)


def board_lines(game, terminal, elapsed_seconds):
    """Return the colored border and current board content."""

    score_value = "{0}/{1}".format(game.score, game.dot_count)
    timer_value = format_time(elapsed_seconds)
    score_plain = "Score: " + score_value
    timer_plain = "Time: " + timer_value
    score = "Score: " + terminal.color("v", score_value)
    timer = "Time: " + terminal.color("v", timer_value)
    lines = [
        score + " " * (game.width + 2 - len(score_plain) - len(timer_plain)) + timer,
        "╔" + "═" * game.width + "╗",
    ]
    for y in range(game.height):
        row = []  # type: List[str]
        for x in range(game.width):
            position = (x, y)
            if position == game.player:
                row.append(terminal.color("y", "*"))
            elif game.snake and position in game.snake_body:
                row.append(terminal.color("y", "o"))
            elif position in game.dots:
                row.append(terminal.color("g", game.dot_symbol))
            else:
                row.append(" ")
        lines.append("║" + "".join(row) + "║")
    lines.extend([
        "╚" + "═" * game.width + "╝",
        "Arrows: move | Q: quit",
    ])
    return lines


def draw(game, terminal, redraw, elapsed_seconds):
    """Draw the board, replacing the prior frame when ANSI is supported."""

    use_cursor = redraw and ansi_enabled()
    if use_cursor:
        cursor_up(game.height + 4)

    for line in board_lines(game, terminal, elapsed_seconds):
        if use_cursor:
            clear_line()
        print(line)


def main():
    """Run one game."""

    try:
        config = load_config()
    except ValueError as error:
        print("Configuration error: {0}".format(error))
        return 1

    terminal = Terminal()
    game = Game.new(config)
    started_at = time.monotonic()
    last_shown_second = 0
    draw(game, terminal, redraw=False, elapsed_seconds=0)

    while game.dots:
        elapsed_seconds = int(time.monotonic() - started_at)
        direction = read_direction()
        if direction is None:
            print("Game aborted.")
            return 0
        if direction:
            game.move(*direction)
            draw(game, terminal, redraw=True, elapsed_seconds=elapsed_seconds)
            last_shown_second = elapsed_seconds
        elif elapsed_seconds != last_shown_second:
            draw(game, terminal, redraw=True, elapsed_seconds=elapsed_seconds)
            last_shown_second = elapsed_seconds
        time.sleep(0.03)

    print("You won in {0}! You collected {1} points.".format(
        format_time(elapsed_seconds), game.score
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
