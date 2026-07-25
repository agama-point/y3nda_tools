"""Reusable, safe runner for project-local Python command flows."""

import shlex
import subprocess
import sys
from collections import namedtuple
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


__version__ = "0.26.03"


PYTHON_LAUNCHERS = {"py", "py.exe", "python", "python.exe", "python3", "python3.exe"}


class FlowError(ValueError):
    """Report an invalid flow file or command."""


class FlowCommand(namedtuple("_FlowCommand", "line_number display_arguments execution_arguments")):
    """One validated project-local Python command."""

    __slots__ = ()

    @property
    def display_text(self) -> str:
        """Return a readable command line for terminal output."""

        return subprocess.list2cmdline(self.display_arguments)


class FlowRunner:
    """Load, validate, and run Python-only flows inside one project root."""

    def __init__(
        self,
        project_root: Path,
        python_executable: Optional[str] = None,
        flow_directories: Optional[Sequence[Path]] = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.python_executable = python_executable or sys.executable
        directories = [self.project_root]  # type: List[Path]
        for directory in flow_directories or ():
            resolved_directory = Path(directory).resolve()
            self._require_inside_project(
                resolved_directory,
                "A flow directory must remain inside the repository.",
            )
            if resolved_directory not in directories:
                directories.append(resolved_directory)
        self.flow_directories = tuple(directories)  # type: Tuple[Path, ...]

    def resolve_flow_path(self, configured_path: Path) -> Path:
        """Resolve a flow path and require it to remain inside the project."""

        configured_path = Path(configured_path)
        if configured_path.is_absolute():
            flow_path = configured_path.resolve()
            self._require_inside_project(flow_path, "The flow file must remain inside the repository.")
            if flow_path.is_file():
                return flow_path
            raise FlowError(f"Flow file does not exist: {flow_path}")

        for directory in self.flow_directories:
            flow_path = (directory / configured_path).resolve()
            self._require_inside_project(flow_path, "The flow file must remain inside the repository.")
            if flow_path.is_file():
                return flow_path
        raise FlowError(f"Flow file does not exist: {configured_path}")

    def load(self, flow_path: Path) -> List[FlowCommand]:
        """Load and validate every active command before executing the flow."""

        try:
            lines = flow_path.read_text(encoding="utf-8-sig").splitlines()
        except OSError as error:
            raise FlowError(f"Could not read flow file {flow_path}: {error}") from error

        commands = []  # type: List[FlowCommand]
        for line_number, line in enumerate(lines, start=1):
            arguments = self._split_command(line, flow_path, line_number)
            if arguments:
                commands.append(self._validate_command(arguments, flow_path, line_number))

        if not commands:
            raise FlowError(f"Flow file contains no commands: {flow_path}")
        return commands

    def run(self, flow_path: Path, commands: Sequence[FlowCommand], dry_run: bool = False) -> int:
        """Print and optionally execute validated commands in sequence."""

        mode = "Dry run" if dry_run else "Flow"
        print(f"{mode}: {flow_path.name}", flush=True)
        print(f"Working directory: {self.project_root}", flush=True)

        total = len(commands)
        for index, command in enumerate(commands, start=1):
            print(f"[{index}/{total}] line {command.line_number}: {command.display_text}", flush=True)
            if dry_run:
                continue

            try:
                result = subprocess.run(command.execution_arguments, cwd=self.project_root, check=False)
            except OSError as error:
                print(f"ERROR: Could not start step {index}: {error}", file=sys.stderr)
                return 1

            print(f"[{index}/{total}] exit code: {result.returncode}", flush=True)
            if result.returncode:
                print(
                    f"ERROR: Flow stopped at step {index} with exit code {result.returncode}.",
                    file=sys.stderr,
                )
                return result.returncode

        if dry_run:
            print(f"Dry run completed: {total} command(s) validated.", flush=True)
        else:
            print(f"Flow completed successfully: {total} step(s).", flush=True)
        return 0

    def _split_command(self, line: str, flow_path: Path, line_number: int) -> List[str]:
        """Split one command while preserving Windows path backslashes."""

        lexer = shlex.shlex(line, posix=True)
        lexer.whitespace_split = True
        lexer.commenters = "#"
        lexer.escape = ""
        try:
            return list(lexer)
        except ValueError as error:
            raise FlowError(f"{flow_path.name}:{line_number}: {error}") from error

    def _validate_command(
        self,
        arguments: List[str],
        flow_path: Path,
        line_number: int,
    ) -> FlowCommand:
        """Allow Python scripts located anywhere inside the project."""

        location = f"{flow_path.name}:{line_number}"
        if len(arguments) < 2:
            raise FlowError(f"{location}: expected 'python script.py [arguments]'")

        if Path(arguments[0]).name.lower() not in PYTHON_LAUNCHERS:
            raise FlowError(f"{location}: only Python commands are allowed")

        configured_script = Path(arguments[1])
        script_path = (
            configured_script.resolve()
            if configured_script.is_absolute()
            else (self.project_root / configured_script).resolve()
        )
        try:
            relative_script_path = script_path.relative_to(self.project_root)
        except ValueError as error:
            raise FlowError(f"{location}: the script must remain inside the repository") from error
        if script_path.suffix.lower() != ".py":
            raise FlowError(f"{location}: only Python .py scripts are allowed")
        if not script_path.is_file():
            raise FlowError(f"{location}: script does not exist: {relative_script_path}")

        return FlowCommand(
            line_number=line_number,
            display_arguments=("python", str(relative_script_path), *arguments[2:]),
            execution_arguments=(self.python_executable, str(script_path), *arguments[2:]),
        )

    def _require_inside_project(self, path: Path, message: str) -> None:
        try:
            path.relative_to(self.project_root)
        except ValueError as error:
            raise FlowError(message) from error
