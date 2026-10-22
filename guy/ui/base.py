from abc import ABC, abstractmethod
from collections.abc import Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class Suggestion:
    """One autocomplete entry (e.g. a slash command or a session to resume)."""

    value: str
    label: str
    meta: str = ""


class CompletionSource(Protocol):
    """Supplied by the app so the UI never knows about sessions or commands."""

    def complete(self, text: str) -> Sequence[Suggestion]: ...


class ResponseStream(ABC):
    @abstractmethod
    def append(self, delta: str) -> None: ...

    @abstractmethod
    def finish(self) -> None: ...


class ToolRun(ABC):
    id: str  # short id, used by /tool <id>

    @abstractmethod
    def append_output(self, chunk: str) -> None:
        """Live output. The UI keeps the FULL output for later expansion."""

    @abstractmethod
    def finish(self, *, ok: bool, summary: str = "") -> None: ...


class UserInterface(ABC):
    """Contract between the agent harness and any UI implementation."""

    # --- input (async: the harness runs inside an event loop) ---
    @abstractmethod
    async def get_input(self, prompt: str = "") -> str:
        """Raises EOFError on Ctrl+D; KeyboardInterrupt on Ctrl+C."""

    @abstractmethod
    async def ask_permission(self, prompt: str, *, danger: bool = False) -> bool: ...

    @abstractmethod
    async def select_option(self, prompt: str, options: Sequence[str]) -> int | None:
        """Returns the selected index, or None if cancelled."""

    @abstractmethod
    def set_completion_source(self, source: CompletionSource) -> None: ...

    # --- output ---
    @abstractmethod
    def display_message(self, message: str, sender: str | None = None) -> None:
        """Static, complete message (user echo, system text)."""

    @abstractmethod
    def begin_response(self) -> ResponseStream:
        """Streamed assistant text."""

    @abstractmethod
    def begin_tool(self, name: str, args: dict[str, Any]) -> ToolRun: ...

    @abstractmethod
    async def show_tool_output(self, tool_id: str | None = None) -> None:
        """Open the full output of a finished tool (None = the latest)."""

    @abstractmethod
    def thinking(self, label: str | None = None) -> AbstractContextManager[None]: ...

    @abstractmethod
    def display_warning(self, warn_message: str) -> None: ...

    @abstractmethod
    def display_error(self, error_message: str) -> None: ...

    @abstractmethod
    def display_success(self, success_message: str) -> None: ...

    @abstractmethod
    def set_status(self, **fields: str) -> None:
        """Bottom toolbar fields: model, cwd, tokens, ..."""
