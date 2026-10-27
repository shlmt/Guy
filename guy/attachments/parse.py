import re

from .base import Ref

_REF = re.compile(r'(?<!\S)#(?:"([^"]+)"|(\S+?))(?::(\d+)(-)?(\d*))?(?=\s|$)')


def parse_refs(text: str) -> list[Ref]:
    refs = []
    for m in _REF.finditer(text):
        quoted, bare, start, dash, end = m.groups()
        s = int(start) if start else None
        e = (int(end) if end else None) if dash else s
        refs.append(Ref(m.group(0)[1:], quoted or bare, s, e))
    return refs
