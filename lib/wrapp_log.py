"""Small, reusable console-to-file logging helper for the examples."""

import json
import re
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, TextIO


__version__ = "0.26.02"


ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


class _Tee:
    """Send text to the original console stream and a log file."""

    def __init__(self, stream: TextIO, log_file: TextIO) -> None:
        self._stream = stream
        self._log_file = log_file

    def write(self, text: str) -> int:
        written = self._stream.write(text)
        self._log_file.write(ANSI_ESCAPE.sub("", text))
        return written

    def flush(self) -> None:
        self._stream.flush()
        self._log_file.flush()

    def isatty(self) -> bool:
        return self._stream.isatty()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._stream, name)


def load_json_object(path: Path) -> Dict[str, object]:
    """Read a JSON object from ``path`` with command-line friendly errors."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"Cannot read configuration {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Configuration is not valid JSON: {path}: {error}") from error

    if not isinstance(data, dict):
        raise ValueError(f"Configuration must contain a JSON object: {path}")
    return data


def load_config(config_path: Path) -> Dict[str, object]:
    """Read and validate the small y3nda JSON configuration."""

    data = load_json_object(config_path)

    subdir = data.get("subdir")
    if not isinstance(subdir, str) or not subdir.strip():
        raise ValueError(f"'subdir' must be non-empty text: {config_path}")

    log_enabled = data.get("log", False)
    if not isinstance(log_enabled, bool):
        raise ValueError(f"'log' must be true or false: {config_path}")

    return data


def get_project_directory(project_root: Path, config: Dict[str, object]) -> Path:
    """Resolve the configured project directory and keep it inside the project."""

    subdir = Path(str(config["subdir"]))
    if subdir.is_absolute():
        raise ValueError("'subdir' must be a relative path")

    root = project_root.resolve()
    project_directory = (root / subdir).resolve()
    try:
        project_directory.relative_to(root)
    except ValueError as error:
        raise ValueError("'subdir' must point inside the project root") from error

    project_directory.mkdir(parents=True, exist_ok=True)
    return project_directory


@contextmanager
def console_log(project_directory: Path, program_name: str, enabled: bool) -> Iterator[None]:
    """Mirror stdout and stderr to ``log.txt`` only when logging is enabled."""

    if not enabled:
        yield
        return

    log_path = project_directory / "log.txt"
    with log_path.open("a", encoding="utf-8") as log_file:
        if log_path.stat().st_size:
            log_file.write("\n")
        log_file.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} [{program_name}]\n")
        log_file.flush()

        original_stdout, original_stderr = sys.stdout, sys.stderr
        sys.stdout = _Tee(original_stdout, log_file)  # type: ignore[assignment]
        sys.stderr = _Tee(original_stderr, log_file)  # type: ignore[assignment]
        try:
            yield
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
            sys.stdout, sys.stderr = original_stdout, original_stderr
            log_file.write("\n---\n")
