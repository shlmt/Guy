from .base import Command, CommandContext, CommandError


async def _exit(ctx: CommandContext, args: tuple[str, ...]) -> None:
    if args:
        raise CommandError("usage: /exit")
    ctx.harness.stop()


COMMANDS = (Command("exit", _exit, "Exit the CLI", "/exit"),)
