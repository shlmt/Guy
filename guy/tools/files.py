from pydantic_ai import RunContext

from ..ui import app_ui
from .deps import Deps

MAX_OUTPUT = 10_000


def read_file(ctx: RunContext[Deps], file: str, offset: int = 0, limit: int = MAX_OUTPUT) -> str:
    """Read a file and return its text from `offset` for `limit` chars."""

    app_ui.display_message(f"read file: {file}, offset: {offset}, limit: {limit}", "Tool")

    try:
        path = ctx.deps.resolve_work_path(file)
        if not path.is_file():
            return f"Error: no such file: {file}"
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[offset : offset + limit]

    except Exception as e:
        print(f"Error reading file: {e}")
        return e


def write_file(ctx: RunContext[Deps], file: str, new_content: str) -> str:
    """Create `file` or replace its entire contents with `new_content`."""
    app_ui.display_message(f"write file: {file}, new content length: {len(new_content)}", "Tool")

    try:
        path = ctx.deps.resolve_work_path(file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_content, encoding="utf-8")
        return f"Wrote {len(new_content)} chars to {file}"

    except Exception as e:
        print(f"Error writing file: {e}")
        return e


def edit_file(ctx: RunContext[Deps], file: str, existing_text: str, replacement_text: str) -> str:
    """Replace the single, exact occurrence of `existing_text` in `file`."""
    app_ui.display_message(f"edit file: {file}", "Tool")

    try:
        path = ctx.deps.resolve_work_path(file)
        if not path.is_file():
            return f"Error: no such file: {file}"
        text = path.read_text(encoding="utf-8")
        count = text.count(existing_text)
        if count == 0:
            return f"Error: existing_text not found in {file}"
        if count > 1:
            return f"Error: existing_text appears {count} times in {file}; add more surrounding context to make it unique"
        path.write_text(text.replace(existing_text, replacement_text), encoding="utf-8")
        return f"Edited {file}"

    except Exception as e:
        print(f"Error editing file: {e}")
        return e
