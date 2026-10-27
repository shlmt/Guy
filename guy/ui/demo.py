"""Scripted fake session exercising every UserInterface method: python -m guy.ui.demo"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input

from .base import Suggestion
from .rich import RichUserInterface

REPLY = """\
I found the bug in `config.py`:

- `load()` reads the file **before** the path is resolved
- the fallback silently swallows `FileNotFoundError`

```python
path = resolve(path)
return json.loads(path.read_text())
```
"""

TOOL_OUTPUT = [f"tests/test_config.py::test_case_{n} PASSED\n" for n in range(1, 25)]


class DemoSource:
    COMMANDS = ("/help", "/tool", "/resume", "/clear")

    def complete(self, text: str) -> Sequence[Suggestion]:
        return (
            [Suggestion(c, c, "command") for c in self.COMMANDS if c.startswith(text)]
            if text
            else []
        )


async def main() -> None:
    loop = asyncio.get_running_loop()
    with create_pipe_input() as keys, create_app_session(input=keys):
        ui = RichUserInterface()

        def type_later(text: str, delay: float = 0.8) -> None:
            loop.call_later(delay, keys.send_text, text)

        ui.set_completion_source(DemoSource())
        ui.set_status(model="gemini-2.5", cwd="~/project", tokens="0")
        ui.display_message("session resumed")

        type_later("/he")
        type_later("\t", 1.3)
        type_later("\r", 2.0)
        command = await ui.get_input()
        ui.display_message(command, sender="you")

        with ui.thinking("reading the codebase"):
            await asyncio.sleep(2)
            stream = ui.begin_response()
            for word in REPLY.split(" "):
                stream.append(word + " ")
                await asyncio.sleep(0.05)
            stream.finish()
        ui.set_status(tokens="1.2k")

        type_later("y")
        if await ui.ask_permission("Run `pytest -q` in the project?", danger=False):
            tool = ui.begin_tool("run_command", {"command": "pytest -q", "cwd": "."})
            for line in TOOL_OUTPUT:
                tool.append_output(line)
                await asyncio.sleep(0.12)
            tool.finish(ok=True, summary="24 passed")

        type_later("q")
        await ui.show_tool_output()

        type_later("2")
        options = ["Apply and run tests", "Show diff"]
        choice = await ui.select_option("Apply the fix?", options)
        ui.display_message(f"selected index {options.index(choice)}")

        type_later("n")
        await ui.ask_permission("Delete build/ directory?", danger=True)

        failing = ui.begin_tool("write_file", {"path": "/etc/hosts"})
        await asyncio.sleep(1)
        failing.append_output("permission denied\n")
        failing.finish(ok=False, summary="permission denied")

        ui.display_warning("context is 80% full")
        ui.display_error("model request failed: 503")
        ui.display_success("all tests passed")
        ui.set_status(tokens="")


if __name__ == "__main__":
    asyncio.run(main())
