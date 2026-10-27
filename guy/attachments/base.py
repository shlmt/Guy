"""Shared types. Resolvers and the parser both depend on this, never on each other."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pydantic_ai import BinaryContent, TextContent, UserContent

TAG = "attachment:"


class AttachmentError(Exception): ...


@dataclass(frozen=True, slots=True)
class Ref:
    raw: str
    target: str
    start: int | None = None
    end: int | None = None  # None with start set = to EOF


@dataclass(frozen=True, slots=True)
class Attachment:
    label: str
    parts: list[UserContent]


class Resolver(Protocol):
    def __call__(self, ref: Ref, work_dir: Path, /) -> Attachment | None: ...


def text_part(content: str, label: str) -> TextContent:
    return TextContent(content, metadata={"attachment": label})


def binary_part(data: bytes, media_type: str, label: str) -> BinaryContent:
    return BinaryContent(data, media_type=media_type, identifier=TAG + label)


def label_of(part: UserContent) -> str | None:
    """Non-None = part came from a #ref (sessions replace it with a placeholder on save)."""
    if isinstance(part, TextContent) and isinstance(part.metadata, dict):
        return part.metadata.get("attachment")
    if isinstance(part, BinaryContent) and part.identifier and part.identifier.startswith(TAG):
        return part.identifier[len(TAG) :]
    return None
