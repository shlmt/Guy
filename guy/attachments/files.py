import mimetypes
from pathlib import Path

from .base import Attachment, AttachmentError, Ref, binary_part, text_part

MAX_TEXT = 200_000
MAX_BINARY = 20_000_000


def resolve(ref: Ref, work_dir: Path) -> Attachment | None:
    path = (work_dir / Path(ref.target).expanduser()).resolve()
    if not path.is_file():
        return None
    size = path.stat().st_size
    mime = mimetypes.guess_type(path)[0] or ""
    if mime.startswith("image/") or mime == "application/pdf":
        if size > MAX_BINARY:
            raise AttachmentError(f"{path.name}: too large")
        return Attachment(ref.raw, [binary_part(path.read_bytes(), mime, ref.raw)])
    if size > MAX_TEXT:
        raise AttachmentError(f"{path.name}: too large")
    try:
        lines = path.read_text().splitlines()
    except UnicodeDecodeError:
        raise AttachmentError(f"{path.name}: unsupported file") from None
    rng = ""
    if ref.start:
        lines = lines[ref.start - 1 : ref.end]
        rng = f' lines="{ref.start}-{ref.end or ""}"'
    body = "\n".join(lines)
    text = f'<attachment path="{path}"{rng}>\n{body}\n</attachment>'
    return Attachment(ref.raw, [text_part(text, ref.raw)])
