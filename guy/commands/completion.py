from collections.abc import Sequence

from ..ui.base import CompletionSource, Suggestion
from .base import CommandContext
from .registry import CommandRegistry


class CommandCompletionSource(CompletionSource):
    """Adapts a CommandRegistry to the UI's CompletionSource."""

    def __init__(self, registry: CommandRegistry, ctx: CommandContext) -> None:
        self._registry = registry
        self._ctx = ctx

    def complete(self, text: str) -> Sequence[Suggestion]:
        return self._registry.complete(text, self._ctx)
