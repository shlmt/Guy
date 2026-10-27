import re
from collections.abc import Iterator
from pathlib import Path

from pydantic_ai import RunContext

from ..ui import app_ui
from .deps import Deps

MAX_RESULTS = 200
IGNORED_DIRS = {".git", ".guy", ".venv", "node_modules", "__pycache__"}


def _files(base: Path, pattern: str) -> Iterator[Path]:
    for path in sorted(base.glob(pattern)):
        if path.is_file() and not IGNORED_DIRS.intersection(path.relative_to(base).parts):
            yield path


def _get_relative_path(ctx: RunContext[Deps], path: Path) -> str:
    return path.relative_to(ctx.deps.work_dir.resolve()).as_posix()


def search_files(ctx: RunContext[Deps], pattern: str) -> str:
    """List files matching a glob pattern relative to the project root, e.g. 'src/**/*.py'."""

    app_ui.display_message("search files with pattern: " + pattern, "Tool")

    try:
        root = ctx.deps.resolve_work_path(".")
        matches = [_get_relative_path(ctx, p) for p in _files(root, pattern)]
        if not matches:
            return "No files matched."
        out = "\n".join(matches[:MAX_RESULTS])
        if len(matches) > MAX_RESULTS:
            out += f"\n[{len(matches) - MAX_RESULTS} more not shown; narrow the pattern]"
        return out
    except Exception as e:
        print(f"Error searching files: {e}")
        return e


def search_content(
    ctx: RunContext[Deps], pattern: str, ignore_case: bool = False, include: str = "**/*"
) -> str:
    """
    Search file contents with a regex. Returns 'path:line: text' for each match.
    Use `include` to limit files, e.g. '**/*.py'.
    Use `ignore_casew when needed.
    """
    suffix = ", case ignored." if ignore_case else ""
    app_ui.display_message(
        f"search content with pattern: {pattern}, include: {include}{suffix}", "Tool"
    )
    try:
        regex = re.compile(pattern, re.IGNORECASE if ignore_case else 0)
    except re.error as exc:
        return f"Error: invalid regex: {exc}"

    try:
        root = ctx.deps.resolve_work_path(".")
        results: list[str] = []
        for path in _files(root, include):
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue  # binary or unreadable
            for n, line in enumerate(text.splitlines(), 1):
                if regex.search(line):
                    results.append(f"{_get_relative_path(ctx, path)}:{n}: {line.strip()[:200]}")
                    if len(results) >= MAX_RESULTS:
                        return "\n".join(results) + "\n[limit reached; narrow the search]"
        return "\n".join(results) or "No matches."
    except Exception as e:
        print(f"Error searching content: {e}")
        return e


def list_dir(
    ctx: RunContext[Deps], path: str = ".", depth: int = 1, only_folders: bool = False
) -> str:
    """
    List files and folders under `path` (relative to project root), up to `depth` levels.
    Use `only_folders=True` to list only directories. Ignores common ignored directories.
    """
    suffix = ", only folders" if only_folders else ""
    app_ui.display_message(f"list directory: {path}, depth: {depth}{suffix}", "Tool")

    try:
        root = ctx.deps.resolve_work_path(path)
        if not root.is_dir():
            return f"Error: not a directory: {path}"

        lines: list[str] = []

        def walk(directory: Path, level: int) -> None:
            for entry in sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name)):
                if entry.name in IGNORED_DIRS:
                    continue

                is_dir = entry.is_dir()
                if only_folders and not is_dir:
                    continue

                suffix = "/" if is_dir else ""
                lines.append(f"{'  ' * level}{entry.name}{suffix}")

                if is_dir and level + 1 < depth:
                    walk(entry, level + 1)

        walk(root, 0)

        if len(lines) > MAX_RESULTS:
            return "\n".join(lines[:MAX_RESULTS]) + "\n[truncated; use a subfolder or lower depth]"

        return "\n".join(lines) or "(empty)"

    except Exception as e:
        print(f"Error listing directory: {e}")
        return e
