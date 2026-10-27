from ..commands.base import Command, CommandContext, CommandError, ParsedLine, Suggestion


def _session_candidates(ctx: CommandContext, parsed: ParsedLine) -> list[Suggestion]:
    return [
        Suggestion(s.id, s.title, f"{s.updated_at:%Y-%m-%d %H:%M}")
        for s in ctx.harness.session_store.recent()
    ]


def _resume_candidates(ctx: CommandContext, parsed: ParsedLine) -> list[Suggestion]:
    return [] if parsed.args else _session_candidates(ctx, parsed)


def _rename_candidates(ctx: CommandContext, parsed: ParsedLine) -> list[Suggestion]:
    return _session_candidates(ctx, parsed) if len(parsed.args) == 1 else []


async def _new(ctx: CommandContext, args: tuple[str, ...]) -> None:
    if args:
        raise CommandError("usage: /new")
    ctx.harness.new_session()
    ctx.ui.display_success("Started a new session")


async def _resume(ctx: CommandContext, args: tuple[str, ...]) -> None:
    if len(args) != 1:
        raise CommandError("usage: /resume <session-id>")
    try:
        ctx.harness.resume_session(args[0])
    except FileNotFoundError:
        raise CommandError(f"no such session: {args[0]}") from None
    ctx.ui.display_success(f"Resumed {args[0]}")


async def _rename(ctx: CommandContext, args: tuple[str, ...]) -> None:
    if not 1 <= len(args) <= 2:
        raise CommandError("usage: /rename <title> [session-id]")
    title, *target = args
    session_id = target[0] if target else ctx.harness.session_id
    try:
        ctx.harness.session_store.set_title(session_id, title)
    except FileNotFoundError:
        raise CommandError(f"no such session: {session_id}") from None
    ctx.ui.display_success(f"Renamed {session_id} to {title!r}")


COMMANDS = (
    Command("new", _new, "Start a new session", "/new"),
    Command(
        "resume", _resume, "Resume a saved session", "/resume <session-id>", _resume_candidates
    ),
    Command(
        "rename",
        _rename,
        "Rename a session (default: current)",
        "/rename <title> [session-id]",
        _rename_candidates,
    ),
)
