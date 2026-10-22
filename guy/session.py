"""
Session persistence.
One JSONL file per session:
    line 1   header (_Header)       - session metadata, rewritten only on change
    line 2+  one ModelMessage each  - append-only

created time lives in the id (file name),
last-updated time is the file's mtime,
"""

import os
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from pydantic import BaseModel
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from .paths import SESSION_DIR

DEFAULT_TITLE = "New session"

# --- What is saved per message line: the one place to tune it. ---------------
# Top-level message fields to drop (only fields that have defaults can be dropped).
# `instructions` is re-sent in every request but is rebuilt from the agent on each run.
_EXCLUDE = {"__all__": {"instructions"}}
# -----------------------------------------------------------------------------


class _Header(BaseModel):
    version: int = 1
    title: str = DEFAULT_TITLE

    @classmethod
    def from_line(cls, line: str) -> "_Header":
        """Parse the first line of a session file; a damaged header falls back to defaults."""
        try:
            return cls.model_validate_json(line)
        except ValueError:
            return cls()


@dataclass(frozen=True, slots=True)
class SessionInfo:
    id: str
    title: str
    updated_at: datetime


def _encode(message: ModelMessage) -> str:
    # dump_json of a one-item list is "[{...}]": strip the brackets to get one line.
    raw = ModelMessagesTypeAdapter.dump_json([message], exclude=_EXCLUDE, exclude_none=True)
    return raw.decode()[1:-1]


def _decode(line: str) -> ModelMessage:
    return ModelMessagesTypeAdapter.validate_json(f"[{line}]")[0]


class SessionStore:
    def _path(self, session_id: str) -> Path:
        return SESSION_DIR / f"{session_id}.jsonl"

    def info(self, path: Path) -> SessionInfo:
        with path.open(encoding="utf-8") as f:
            header = _Header.from_line(f.readline())
        updated_at = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
        return SessionInfo(path.stem, header.title, updated_at)

    def new_id(self) -> str:
        """Sorts chronologically by creation time."""
        return f"{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:4]}"

    def append(self, session_id: str, messages: Sequence[ModelMessage]) -> None:
        if not messages:
            return

        path = self._path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        is_new = not path.exists()
        with path.open("a", encoding="utf-8") as f:
            if is_new:
                f.write(_Header().model_dump_json() + "\n")
            f.writelines(_encode(m) + "\n" for m in messages)

    def load(self, session_id: str) -> list[ModelMessage]:
        lines = self._path(session_id).read_text(encoding="utf-8").splitlines()[1:]
        messages: list[ModelMessage] = []
        for line in lines:
            try:
                messages.append(_decode(line))
            except ValueError:  # truncated tail after a crash
                break
        return messages

    def set_title(self, session_id: str, title: str) -> None:
        path = self._path(session_id)
        first, *rest = path.read_text(encoding="utf-8").splitlines(keepends=True)
        header = _Header.from_line(first).model_copy(update={"title": title})
        tmp = path.with_suffix(".tmp")  # atomic replace: a crash never loses the session
        tmp.write_text(header.model_dump_json() + "\n" + "".join(rest), encoding="utf-8")
        os.replace(tmp, path)

    def recent(self, limit: int = 10) -> list[SessionInfo]:
        directory = SESSION_DIR
        if not directory.exists():
            return []

        files = sorted(directory.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        return [self.info(f) for f in files[:limit]]


if __name__ == "__main__":
    import time
    from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

    def turn(user: str, ai: str) -> list[ModelMessage]:
        return [
            ModelRequest(parts=[UserPromptPart(content=user)]),
            ModelResponse(parts=[TextPart(content=ai)]),
        ]

    store = SessionStore()

    print("1. Check initial state")
    assert store.recent() == []
    print("   No saved sessions — OK")

    print("\n2. Create a session and add messages")
    first = store.new_id()
    print(f"   Created session: {first}")

    store.append(first, turn("שלום", "היי"))
    print("   Added a user message and an AI response")

    store.append(first, turn("מה המצב?", "הכל טוב"))
    print("   Added two more messages to the same session")

    assert len(store.load(first)) == 4
    print("   Loading the session returned 4 messages — OK")

    print("\n3. Create another session")
    time.sleep(0.05)
    second = store.new_id()
    store.append(second, turn("Second session", "Fine"))
    print(f"   Created another session: {second}")

    sessions = store.recent()
    print("   Sessions ordered from newest to oldest:")
    for session in sessions:
        print(f"   - {session.id}")

    assert [s.id for s in sessions] == [second, first]
    print("   Session order is correct")

    print("\n4. Update the first session's title")
    store.set_title(first, "New title")
    print("   Title updated")

    sessions = store.recent()
    print("   The most recently updated session appears first:")
    print(f"   {sessions[0].id}")

    assert sessions[0].id == first
    print("   Updated session order is correct")

    print("\nAll tests passed successfully!")
