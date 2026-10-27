"""`#ref` tokens in user text -> prompt parts. New kind = new module + one line in RESOLVERS."""

from pathlib import Path

from pydantic_ai import UserContent

from .urls import resolve as url_resolver
from .files import resolve as file_resolver
from .base import Attachment, AttachmentError, Resolver, label_of
from .parse import parse_refs

RESOLVERS: list[Resolver] = [url_resolver, file_resolver]  # order = priority

__all__ = ["AttachmentError", "build_prompt", "label_of"]


def build_prompt(text: str, work_dir: Path) -> tuple[str | list[UserContent], list[str]]:
    """Returns (prompt for agent.run, labels for the UI)."""
    found: list[Attachment] = []
    for ref in parse_refs(text):
        for resolve in RESOLVERS:
            if att := resolve(ref, work_dir):
                found.append(att)
                break
    if not found:
        return text, []
    return [text, *(p for a in found for p in a.parts)], [a.label for a in found]
