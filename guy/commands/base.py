from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from ..session import SessionStore
from ..ui.base import Suggestion, UserInterface


class CommandError(Exception):
    """Recoverable user error (bad args, unknown command); the caller reports it via the UI."""


class CommandHarness(Protocol):
    """What commands need from the harness."""

    session_id: str
    session_store: SessionStore

    def new_session(self) -> None: ...

    def resume_session(self, session_id: str) -> None: ...

    def stop(self) -> None: ...


@dataclass(frozen=True, slots=True)
class CommandContext:
    harness: CommandHarness
    ui: UserInterface


@dataclass(frozen=True, slots=True)
class ParsedLine:
    name: str
    args: tuple[str, ...]
    partial: str = ""  # lenient mode only: the unfinished word under the cursor


Handler = Callable[[CommandContext, tuple[str, ...]], Awaitable[None]]
# Sync, read-only, fast. Receives the parsed line; the registry filters by prefix of `partial`.
Completer = Callable[[CommandContext, ParsedLine], Sequence[Suggestion]]


@dataclass(frozen=True, slots=True)
class Command:
    name: str
    handler: Handler
    help: str
    usage: str = ""
    completer: Completer | None = None
