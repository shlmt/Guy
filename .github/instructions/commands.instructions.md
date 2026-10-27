---
description: Slash-command conventions for the commands layer.
applyTo: '**/commands/**'
---

- Commands are infrastructure; domains are adapters.
- Every domain has its own commands file, e.g., `sessions/commands.py` for the `sessions` domain.
- Registration is explicit in `commands/__init__.py` (like `tools_registry`). No decorators, no hidden imports.
- `Harness` stays slim: loop + session state only.
- `CommandContext` has a typed harness protocol; no `Any`.
- One `self.ctx` in `Harness.__init__`; reuse it.
- `CommandRegistry.dispatch()` owns command errors: catch `CommandError`, show via `ctx.ui`, return the correct boolean.
- `CommandCompletionSource` is the UI bridge; completion is sync, read-only, fast.
- Domain command modules import only from `commands.base`.
- Strict parser by default; lenient parser only for completion.
- Keep commands thin: parse -> call domain -> report via UI.
- No globals, no argparse/click.