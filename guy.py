import asyncio
import os

os.environ["PYDANTIC_AI_NO_BANNER"] = "1"

from guy.agent import build_agent
from guy.commands import CommandCompletionSource, command_registry
from guy.harness import Harness
from guy.paths import WORK_DIR
from guy.session import SessionStore
from guy.tools import Deps, tools_registry
from guy.ui import app_ui


def main() -> None:
    harness = Harness(
        app_ui,
        build_agent(tools_registry.select()),
        Deps(WORK_DIR),
        SessionStore(),
        command_registry,
    )
    app_ui.set_completion_source(CommandCompletionSource(command_registry, harness.ctx))
    asyncio.run(harness.run())


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        exit(1)
