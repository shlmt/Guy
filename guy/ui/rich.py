from __future__ import annotations

import time
from collections.abc import Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application, in_terminal
from prompt_toolkit.completion import Completer, Completion, DynamicCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import FormattedTextControl, HSplit, Layout, Window
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style as PtStyle
from prompt_toolkit.widgets import TextArea
from rich.color import Color
from rich.color_triplet import ColorTriplet
from rich.console import Console, ConsoleOptions, Group, RenderableType, RenderResult
from rich.live import Live
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from .base import CompletionSource, ResponseStream, ToolRun, UserInterface

# --------------------------------------------------------------------------- theme
NAME = "guy"
FPS = 12
TAIL_LINES = 6

THEME = Theme(
    {
        "brand": "bold #1fd1c9",
        "assistant": "bold #1fd1c9",
        "user": "bold #a77bff",
        "text": "#e6f4f2",
        "muted": "#6b8a94",
        "tool.msg": "#b8c4c8",
        "ok": "#3ddc97",
        "fail": "#ff5c7a",
        "warn": "#ffc857",
        "danger": "bold #ff5c7a",
        "tool.name": "bold #7fe7f2",
        "tool.arg": "#5fb8c0",
        "border": "#1c8f98",
        "wave.low": "#117a80",
        "wave.high": "#c4fffa",
        "grad.start": "#2ff3e0",
        "grad.end": "#3b82f6",
        "toolbar": "#a8dcd8 on #0b2a33",
        "toolbar.key": "#6b8a94 on #0b2a33",
        "toolbar.val": "bold #1fd1c9 on #0b2a33",
        "toolbar.brand": "bold #03211f on #1fd1c9",
        "menu": "#e6f4f2",
        "menu.sel": "bold #0f0a1f on #a77bff",
        "viewer": "#e6f4f2",
        "viewer.hint": "#6b8a94 on #0b2a33",
        "markdown.h1": "bold #7ff5ee",
        "markdown.h2": "bold #1fd1c9",
        "markdown.code": "bold #7fe7f2 on #0d2b33",
        "markdown.link": "underline #1fd1c9",
        "markdown.item.bullet": "bold #1fd1c9",
    }
)


@dataclass(frozen=True)
class Symbols:
    prompt: str
    assistant: str
    ok: str
    fail: str
    warn: str
    alarm: str
    info: str
    sep: str
    rule: str
    spinner: str
    logo: tuple[str, ...]


UNICODE = Symbols(
    prompt="❯", assistant="◆", ok="✔", fail="✖", warn="▲", alarm="!", info="●", sep="·",
    rule="─", spinner="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏",
    logo=(
        " ██████╗ ██╗   ██╗██╗   ██╗",
        "██╔════╝ ██║   ██║╚██╗ ██╔╝",
        "██║  ███╗██║   ██║ ╚████╔╝ ",
        "██║   ██║██║   ██║  ╚██╔╝  ",
        "╚██████╔╝╚██████╔╝   ██║   ",
        " ╚═════╝  ╚═════╝    ╚═╝   ",
    ),
)  # fmt: skip
ASCII = Symbols(
    prompt=">", assistant="*", ok="+", fail="x", warn="!", alarm="!!", info="-", sep="|",
    rule="-", spinner="|/-\\", logo=("G U Y",),
)  # fmt: skip


def _rgb(name: str) -> ColorTriplet:
    color = THEME.styles[name].color
    assert color is not None
    return color.get_truecolor()


def _mix(a: ColorTriplet, b: ColorTriplet, t: float) -> Style:
    return Style(color=Color.from_rgb(*(round(x + (y - x) * t) for x, y in zip(a, b))))


def _gradient(text: str) -> Text:
    start, end = _rgb("grad.start"), _rgb("grad.end")
    last = max(len(text) - 1, 1)
    return Text.assemble(*((ch, _mix(start, end, i / last)) for i, ch in enumerate(text)))


def _shimmer(text: str, t: float) -> Text:
    """A bright wave sweeping across the text."""
    low, high = _rgb("wave.low"), _rgb("wave.high")
    center = (t * 14) % (len(text) + 8) - 4
    return Text.assemble(
        *((ch, _mix(low, high, max(0.0, 1 - abs(i - center) / 4))) for i, ch in enumerate(text))
    )


def _pt_style(name: str) -> str:
    """Convert a THEME style to prompt_toolkit syntax, so colors are defined once."""
    style = THEME.styles[name]
    parts = ["bold"] if style.bold else []
    if style.underline:
        parts.append("underline")
    if style.color:
        parts.append(style.color.get_truecolor().hex)
    if style.bgcolor:
        parts.append("bg:" + style.bgcolor.get_truecolor().hex)
    return " ".join(parts)


PT_STYLE = PtStyle.from_dict(
    {
        "prompt.label": _pt_style("user"),
        "prompt.mark": _pt_style("user"),
        "bottom-toolbar": "noreverse " + _pt_style("toolbar"),
        "bottom-toolbar.text": "noreverse " + _pt_style("toolbar"),
        "toolbar.key": _pt_style("toolbar.key"),
        "toolbar.val": _pt_style("toolbar.val"),
        "toolbar.brand": _pt_style("toolbar.brand"),
        "completion-menu.completion": _pt_style("menu"),
        "completion-menu.completion.current": _pt_style("menu.sel"),
        "completion-menu.meta.completion": _pt_style("toolbar.key"),
        "completion-menu.meta.completion.current": _pt_style("toolbar"),
        "menu": _pt_style("menu"),
        "menu.sel": _pt_style("menu.sel"),
        "viewer": _pt_style("viewer"),
        "viewer.title": _pt_style("toolbar.brand"),
        "viewer.hint": _pt_style("viewer.hint"),
    }
)


# --------------------------------------------------------------------- live region
class _LiveRegion:
    """The single Live shared by thinking, response streaming and running tools."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self._live: Live | None = None
        self._views: list[RenderableType] = []

    def add(self, view: RenderableType) -> None:
        self._views.append(view)
        if self._live is None and self.console.is_terminal:
            self._start()

    def remove(self, view: RenderableType, final: RenderableType | None = None) -> None:
        self._views.remove(view)
        if not self._views:
            self._stop()
        if final is not None:
            self.console.print(final)

    @contextmanager
    def suspended(self):
        """Stop the animation while an interactive widget owns the terminal."""
        was_live = self._live is not None
        self._stop()
        try:
            yield
        finally:
            if was_live and self._views:
                self._start()

    def _start(self) -> None:
        self._live = Live(
            get_renderable=lambda: Group(*self._views),
            console=self.console,
            refresh_per_second=FPS,
            transient=True,
        )
        self._live.start()

    def _stop(self) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None


def _short(value: Any, limit: int) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _spin(symbols: Symbols, elapsed: float) -> str:
    return symbols.spinner[int(elapsed * FPS) % len(symbols.spinner)]


class _Thinking:
    def __init__(self, label: str, symbols: Symbols) -> None:
        self._label = label
        self._sym = symbols
        self._start = time.monotonic()

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        elapsed = time.monotonic() - self._start
        line = Text.assemble((_spin(self._sym, elapsed) + " ", "brand"))
        line.append_text(_shimmer(self._label + "...", elapsed))
        line.append(f"  {elapsed:.1f}s", style="muted")
        yield line


class _Response(ResponseStream):
    def __init__(self, region: _LiveRegion, symbols: Symbols) -> None:
        self._region = region
        self._sym = symbols
        self._text = ""
        self._open = True
        region.add(self)

    def append(self, delta: str) -> None:
        if self._open:
            self._text += delta

    def finish(self) -> None:
        if not self._open:
            return
        self._open = False
        self._region.remove(self, self._view() if self._text.strip() else None)

    def _view(self) -> RenderableType:
        grid = Table.grid(padding=(0, 1), expand=True)
        grid.add_column(no_wrap=True)
        grid.add_column(ratio=1)
        grid.add_row(Text(f"{NAME} {self._sym.prompt}", style="assistant"), Markdown(self._text))
        return grid

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        # Only the tail fits the live area; the full text is printed on finish.
        lines = console.render_lines(self._view(), options, pad=False, new_lines=True)
        for line in lines[-max(console.height - 4, 4) :]:
            yield from line


class _ToolLog:
    """Tool messages of one turn: a live tail, collapsed once the answer starts."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        text = "\n".join(self.lines[-TAIL_LINES:])
        yield Text(text, style="tool.msg", no_wrap=True, overflow="ellipsis")


class _Tool(ToolRun):
    def __init__(
        self,
        region: _LiveRegion,
        store: dict[str, tuple[str, str]],
        name: str,
        args: dict[str, Any],
        symbols: Symbols,
    ) -> None:
        self.id = uuid4().hex[:4]
        self._region = region
        self._store = store
        self._sym = symbols
        self._name = name
        self._args = _short(", ".join(f"{k}={_short(v, 30)}" for k, v in args.items()), 70)
        self._output = ""
        self._open = True
        self._start = time.monotonic()
        region.add(self)

    def append_output(self, chunk: str) -> None:
        if self._open:
            self._output += chunk

    def finish(self, *, ok: bool, summary: str = "") -> None:
        if not self._open:
            return
        self._open = False
        self._store[self.id] = (f"{self._name} {self._args}  #{self.id}", self._output)
        style = "ok" if ok else "fail"
        line = Text.assemble(
            (f"{self._sym.ok if ok else self._sym.fail} ", style),
            (self._name, "tool.name"),
            (f" {self._args}", "tool.arg"),
        )
        if summary:
            line.append(f"  {summary}")
        line.append(f"  {time.monotonic() - self._start:.1f}s  #{self.id}", style="muted")
        self._region.remove(self, line)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        elapsed = time.monotonic() - self._start
        tail = self._output.splitlines()[-TAIL_LINES:]
        body = Text("\n".join(tail) or "...", style="tool.arg", no_wrap=True, overflow="ellipsis")
        title = Text.assemble(
            (_spin(self._sym, elapsed) + " ", "brand"),
            (self._name, "tool.name"),
            (f" {self._args}", "tool.arg"),
        )
        yield Panel(
            body,
            title=title,
            title_align="left",
            subtitle=Text(f"{elapsed:.1f}s", style="muted"),
            subtitle_align="right",
            border_style="border",
            padding=(0, 1),
        )


class _SourceCompleter(Completer):
    def __init__(self, source: CompletionSource) -> None:
        self._source = source

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        for item in self._source.complete(text):
            yield Completion(
                item.value, start_position=-len(text), display=item.label, display_meta=item.meta
            )


# ------------------------------------------------------------------------------ ui
class RichUserInterface(UserInterface):
    def __init__(self, console: Console | None = None, *, show_banner: bool = True) -> None:
        self._console = console or Console()
        self._console.push_theme(THEME)
        self._sym = ASCII if self._console.options.ascii_only else UNICODE
        self._region = _LiveRegion(self._console)
        self._outputs: dict[str, tuple[str, str]] = {}
        self._status: dict[str, str] = {}
        self._tool_log: _ToolLog | None = None
        self._completer: Completer | None = None
        self._session = self._create_session()
        if show_banner and self._console.is_terminal:
            self._print_banner()

    def _create_session(self) -> PromptSession[str]:
        keys = KeyBindings()

        @keys.add("escape", "enter")
        def _newline(event) -> None:
            event.current_buffer.insert_text("\n")

        @keys.add("c-o")
        def _expand(event) -> None:
            async def view() -> None:
                async with in_terminal():
                    await self.show_tool_output()

            event.app.create_background_task(view())

        return PromptSession(
            completer=DynamicCompleter(lambda: self._completer),
            complete_while_typing=True,
            bottom_toolbar=self._toolbar,
            key_bindings=keys,
            style=PT_STYLE,
        )

    def _toolbar(self) -> list[tuple[str, str]]:
        parts = [("class:toolbar.brand", f" {self._sym.assistant} {NAME} ")]
        for key, value in self._status.items():
            parts += [("class:toolbar.key", f"  {key} "), ("class:toolbar.val", value)]
        return parts

    # --- input ---
    async def get_input(self, prompt: str = "") -> str:
        message: list[tuple[str, str]] = []
        if prompt:
            message.append(("class:prompt.label", f"{prompt} "))
        message.append(("class:prompt.mark", f"{self._sym.prompt} "))
        self._collapse_tool_log()
        with patch_stdout(raw=True):
            return await self._session.prompt_async(message)

    async def ask_permission(self, prompt: str, *, danger: bool = False) -> bool:
        icon, risk = (self._sym.alarm, "danger") if danger else (self._sym.warn, "warn")
        title = "dangerous action" if danger else "permission required"
        self._console.print(
            Panel(
                Text(prompt, style="text"),
                title=Text(f"{icon} {title}", style=risk),
                title_align="left",
                border_style="warn",
                padding=(0, 1),
            )
        )
        index = await self._menu(["Allow (y)", "Deny (n)"], default=1, hotkeys=("y", "n"))
        return index == 0

    async def select_option(self, prompt: str, options: Sequence[str]) -> int | None:
        self._console.print(Text(f"{self._sym.prompt} {prompt}", style="user"))
        return await self._menu(options)

    def set_completion_source(self, source: CompletionSource) -> None:
        self._completer = _SourceCompleter(source)

    # --- output ---
    def display_message(self, message: str, sender: str | None = None) -> None:
        if sender == "Tool":
            if self._tool_log is None:
                self._tool_log = _ToolLog()
                self._region.add(self._tool_log)
            self._tool_log.lines.append(f"{self._sym.info} {sender}: {message}")
        elif sender:
            self._console.print(
                Text.assemble(
                    (f"{self._sym.info} {sender}: ", "user"),
                    (message, "text"),
                )
            )
        else:
            self._console.print(Text(f"{self._sym.info} {message}", style="muted"))

    def begin_response(self) -> ResponseStream:
        self._collapse_tool_log()
        return _Response(self._region, self._sym)

    def begin_tool(self, name: str, args: dict[str, Any]) -> ToolRun:
        return _Tool(self._region, self._outputs, name, args, self._sym)

    async def show_tool_output(self, tool_id: str | None = None) -> None:
        key = tool_id.lstrip("#") if tool_id else next(reversed(self._outputs), "")
        if not key or key not in self._outputs:
            self.display_warning(f"no output stored for tool {tool_id or '(latest)'}")
            return
        title, text = self._outputs[key]
        area = TextArea(text=text, read_only=True, scrollbar=True, style="class:viewer")
        hint = f" q close {self._sym.sep} arrows/PgUp/PgDn scroll"
        keys = KeyBindings()
        keys.add("q")(lambda event: event.app.exit())
        keys.add("c-c")(lambda event: event.app.exit())
        layout = Layout(
            HSplit(
                [
                    Window(FormattedTextControl([("class:viewer.title", f" {title} ")]), height=1),
                    area,
                    Window(FormattedTextControl([("class:viewer.hint", hint)]), height=1),
                ]
            ),
            focused_element=area,
        )
        app = Application(layout=layout, key_bindings=keys, style=PT_STYLE, full_screen=True)
        with self._region.suspended():
            await app.run_async()

    @contextmanager
    def thinking(self, label: str | None = None):
        view = _Thinking(label or "thinking", self._sym)
        self._region.add(view)
        try:
            yield
        finally:
            self._region.remove(view)

    def display_warning(self, warn_message: str) -> None:
        self._console.print(Text(f"{self._sym.warn} {warn_message}", style="warn"))

    def display_error(self, error_message: str) -> None:
        self._console.print(
            Panel(
                Text(str(error_message), style="fail"),
                title=Text(f"{self._sym.fail} error", style="danger"),
                title_align="left",
                border_style="fail",
                padding=(0, 1),
            )
        )

    def display_success(self, success_message: str) -> None:
        self._console.print(Text(f"{self._sym.ok} {success_message}", style="ok"))

    def set_status(self, **fields: str) -> None:
        """Updates toolbar fields; an empty value removes the field."""
        for key, value in fields.items():
            if value:
                self._status[key] = value
            else:
                self._status.pop(key, None)
        try:
            if self._session.app.is_running:
                self._session.app.invalidate()
        except Exception:
            pass

    # --- helpers ---
    def _collapse_tool_log(self) -> None:
        log, self._tool_log = self._tool_log, None
        if log is None:
            return
        key = uuid4().hex[:4]
        self._outputs[key] = (f"tool calls  #{key}", "\n".join(log.lines))
        summary = Text.assemble(
            (f"{self._sym.info} {len(log.lines)} tool calls", "tool.msg"),
            (f"  #{key}", "muted"),
            ("  ctrl+o expand", "muted"),
        )
        self._region.remove(log, summary)

    def _print_banner(self) -> None:
        self._console.print()
        for row in self._sym.logo:
            self._console.print(Padding(_gradient(row), (0, 0, 0, 2)))
        sep = f" {self._sym.sep} "
        tagline = sep.join(["AI coding assistant", "developed with ❤️ by shlmt"])
        self._console.print(Padding(Text(tagline, style="muted"), (1, 0, 0, 2)))
        self._console.print()

    async def _menu(
        self, options: Sequence[str], default: int = 0, hotkeys: Sequence[str] = ()
    ) -> int | None:
        """Arrow-key list; returns the chosen index or None on Esc/Ctrl+C."""
        index = default
        keys = KeyBindings()

        def render() -> list[tuple[str, str]]:
            fragments: list[tuple[str, str]] = []
            for i, option in enumerate(options):
                selected = i == index
                pointer = self._sym.prompt if selected else " "
                style = "class:menu.sel" if selected else "class:menu"
                fragments += [(style, f" {pointer} {option} "), ("", "\n")]
            return fragments[:-1]

        @keys.add("up")
        @keys.add("k")
        def _up(event) -> None:
            nonlocal index
            index = (index - 1) % len(options)

        @keys.add("down")
        @keys.add("j")
        def _down(event) -> None:
            nonlocal index
            index = (index + 1) % len(options)

        @keys.add("enter")
        def _accept(event) -> None:
            event.app.exit(result=index)

        @keys.add("escape", eager=True)
        @keys.add("c-c")
        def _cancel(event) -> None:
            event.app.exit(result=None)

        for i, key in enumerate(hotkeys or [str(n) for n in range(1, len(options) + 1)]):
            keys.add(key)(lambda event, i=i: event.app.exit(result=i))

        window = Window(FormattedTextControl(render, show_cursor=False), height=len(options))
        app = Application(
            layout=Layout(window), key_bindings=keys, style=PT_STYLE, erase_when_done=True
        )
        with self._region.suspended():
            return await app.run_async()
