from pathlib import Path

from .base import Attachment, Ref, text_part


def resolve(ref: Ref, _: Path) -> Attachment | None:
    if not ref.target.startswith(("http://", "https://")):
        return None
    hint = f"User referenced URL: {ref.target} (fetch it if needed)"
    return Attachment(ref.raw, [text_part(hint, ref.raw)])
