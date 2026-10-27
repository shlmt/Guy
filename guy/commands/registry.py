from ..ui.base import Suggestion
from .base import Command, CommandContext, CommandError
from .parsing import parse


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        if command.name in self._commands:
            raise ValueError(f"duplicate command: {command.name}")
        self._commands[command.name] = command

    async def dispatch(self, line: str, ctx: CommandContext) -> bool:
        """False if `line` is not a slash command (the caller treats it as a prompt)."""
        try:
            parsed = parse(line)
            if parsed is None:
                return False
            command = self._commands.get(parsed.name)
            if command is None:
                raise CommandError(f"unknown command: /{parsed.name}")
            await command.handler(ctx, parsed.args)
        except CommandError as err:
            ctx.ui.display_error(str(err))
        return True

    def complete(self, line: str, ctx: CommandContext) -> list[Suggestion]:
        try:
            parsed = parse(line, lenient=True)
        except CommandError:
            return []
        if parsed is None:
            return []
        if not parsed.name:
            found = [
                Suggestion(f"/{c.name}", c.usage or f"/{c.name}", c.help)
                for c in self._commands.values()
            ]
            return [c for c in found if c.value.startswith(f"/{parsed.partial}")]
        command = self._commands.get(parsed.name)
        if command is None or command.completer is None:
            return []
        # The UI replaces the whole input line with `value`, so keep the typed prefix.
        head = line[: len(line) - len(parsed.partial)]
        return [
            Suggestion(head + c.value, c.label, c.meta)
            for c in command.completer(ctx, parsed)
            if c.value.startswith(parsed.partial)
        ]
