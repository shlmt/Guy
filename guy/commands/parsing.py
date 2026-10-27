import shlex

from .base import CommandError, ParsedLine


def _split(text: str, lenient: bool) -> list[str]:
    try:
        return shlex.split(text)
    except ValueError as err:  # unbalanced quote
        if not lenient:
            raise CommandError(str(err)) from err
    for quote in ('"', "'"):  # user is still typing: close the quote for them
        try:
            return shlex.split(text + quote)
        except ValueError:
            continue
    raise CommandError("cannot parse line")


def parse(line: str, lenient: bool = False) -> ParsedLine | None:
    """None if `line` is not a slash command.

    Lenient mode (completion) tolerates open quotes and splits off the word being typed
    into `partial`; with "/ne" name is "" and partial is "ne".
    """
    if not line.startswith("/"):
        return None
    body = line[1:]
    tokens = _split(body, lenient)
    partial = ""
    if lenient and (not body or not body[-1].isspace()):
        partial = tokens.pop() if tokens else ""
    if not tokens:
        if lenient:
            return ParsedLine("", (), partial)
        raise CommandError("missing command name")
    return ParsedLine(tokens[0], tuple(tokens[1:]), partial)
