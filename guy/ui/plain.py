from __future__ import annotations

from collections.abc import Sequence
from contextlib import contextmanager
from typing import Any

from .base import CompletionSource, ResponseStream, ToolRun, UserInterface

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"


class PlainResponseStream(ResponseStream):
    def __init__(self) -> None:
        self._open = True
        print(f"{CYAN}{BOLD}Guy:{RESET} ", end="", flush=True)

    def append(self, delta: str) -> None:
        if self._open:
            print(delta, end="", flush=True)

    def finish(self) -> None:
        if self._open:
            self._open = False
            print()


class PlainToolRun(ToolRun):
    def __init__(self, name: str, args: dict[str, Any]) -> None:
        self.name = name
        self.args = args
        self.id = name.lower().replace(" ", "-")
        self._open = True
        print(f"{YELLOW}🔧 {name}{RESET} {args}")

    def append_output(self, chunk: str) -> None:
        if self._open:
            print(chunk, end="", flush=True)

    def finish(self, *, ok: bool, summary: str = "") -> None:
        if not self._open:
            return
        self._open = False
        color = GREEN if ok else RED
        icon = "✔" if ok else "✖"
        print(f"\n{color}{icon} {summary}{RESET}")


class PlainUserInterface(UserInterface):
    def __init__(self) -> None:
        self._completion_source: CompletionSource | None = None

    def set_completion_source(self, source: CompletionSource) -> None:
        self._completion_source = source

    def display_message(self, message: str, sender: str | None = None) -> None:
        if sender:
            print(f"{CYAN}ℹ {sender}:{RESET} {message}")
        else:
            print(f"{CYAN}ℹ {message}{RESET}")

    def get_input(self, prompt: str = "") -> str:
        return input(f"{YELLOW}{prompt} ❯{RESET} " if prompt else "")

    def ask_permission(self, prompt: str, *, danger: bool = False) -> bool:
        suffix = f" {RED}[dangerous]{RESET}" if danger else ""
        response = input(f"{MAGENTA}🛡  {prompt}{suffix} [y/N]:{RESET} ").strip().lower()
        return response in {"y", "yes"}

    def select_option(self, prompt: str, options: Sequence[str]) -> int | None:
        print(f"{CYAN}{BOLD}📋 {prompt}:{RESET}")
        for index, option in enumerate(options, start=1):
            print(f"  {YELLOW}{index}){RESET} {option}")

        while True:
            value = input(f"{YELLOW}❯ Select option (1-{len(options)}):{RESET} ").strip()
            if value.isdigit():
                choice = int(value) - 1
                if 0 <= choice < len(options):
                    return choice
            print(f"{RED}✖ Invalid selection. Try again.{RESET}")

    def begin_response(self) -> ResponseStream:
        return PlainResponseStream()

    def begin_tool(self, name: str, args: dict[str, Any]) -> ToolRun:
        return PlainToolRun(name, args)

    async def show_tool_output(self, tool_id: str | None = None) -> None:
        return None

    @contextmanager
    def thinking(self, label: str | None = None) -> Any:
        prefix = label or "thinking"
        print(f"{MAGENTA}⏳ {prefix}...{RESET}", end=" ", flush=True)
        try:
            yield
        finally:
            print(f"{GREEN}done{RESET}")

    def display_warning(self, warn_message: str) -> None:
        print(f"{YELLOW}⚠ {warn_message}{RESET}")

    def display_error(self, error_message: str) -> None:
        print(f"{RED}{BOLD}✖ [ERROR] {error_message}{RESET}")

    def display_success(self, success_message: str) -> None:
        print(f"{GREEN}{BOLD}✔ [SUCCESS] {success_message}{RESET}")

    def set_status(self, **fields: str) -> None:
        if not fields:
            print(f"{CYAN}● idle{RESET}")
            return
        details = ", ".join(f"{key}={value}" for key, value in fields.items())
        print(f"{CYAN}● {details}{RESET}")


if __name__ == "__main__":
    import asyncio

    ui = PlainUserInterface()

    ui.display_message("plain message")
    ui.display_message("message with sender", sender="Guy")
    ui.display_warning("warning demo")
    ui.display_error("error demo")
    ui.display_success("success demo")
    ui.set_status(model="gemini", cwd="C:/work")

    with ui.thinking("working"):
        pass

    stream = ui.begin_response()
    for chunk in ["streamed ", "response"]:
        stream.append(chunk)
    stream.finish()

    tool = ui.begin_tool("run command", {"command": "dir"})
    tool.append_output("line 1\n")
    tool.finish(ok=True, summary="done")

    print("permission:", ui.ask_permission("Allow this action?", danger=True))
    options = ["first", "second"]
    print("selected:", options[ui.select_option("Pick one", options)])
    print("input:", ui.get_input("User"))
    asyncio.run(ui.show_tool_output())
