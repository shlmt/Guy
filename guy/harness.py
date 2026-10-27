from collections.abc import Sequence

from pydantic_ai import Agent, ModelSettings, UserContent
from pydantic_ai.result import StreamedRunResult

from .commands import CommandContext, CommandRegistry
from .models import model_registry
from .session import SessionStore
from .tools import Deps
from .ui import UserInterface
from .attachments import build_prompt


class Harness:
    """The conversation loop. Everything else is injected."""

    def __init__(
        self,
        ui: UserInterface,
        agent: Agent[Deps, str],
        deps: Deps,
        session_store: SessionStore,
        commands: CommandRegistry,
    ) -> None:
        self.ui = ui
        self.agent = agent
        self.deps = deps
        self.session_store = session_store
        self.commands = commands
        self.ctx = CommandContext(self, ui)
        self._running = True
        self.new_session()

    def new_session(self) -> None:
        self.session_id = self.session_store.new_id()
        self.session_history = None

    def resume_session(self, session_id: str) -> None:
        self.session_history = self.session_store.load(session_id)
        self.session_id = session_id

    def stop(self) -> None:
        self._running = False

    async def run(self) -> None:
        while self._running:
            user_input = (await self.ui.get_input("User")).strip()
            if not user_input:
                continue
            if await self.commands.dispatch(user_input, self.ctx):
                continue
            prompt, _ = build_prompt(user_input, self.deps.work_dir)
            await self._run_turn(prompt)

    async def _run_turn(self, user_input: str | Sequence[UserContent]) -> None:
        try:
            async with self.agent.run_stream(
                user_input,
                model=model_registry.get_current_model(),
                message_history=self.session_history,
                deps=self.deps,
                model_settings=ModelSettings(temperature=0.2),
            ) as result:
                await self._stream_output(result)

            self.session_store.append(self.session_id, result.new_messages())
            if not self.session_history:
                title_input = str(user_input[0]) if not isinstance(user_input, str) else user_input
                self.session_store.set_title(self.session_id, title_input[:50])

            self.session_history = result.all_messages()

        except Exception as err:
            self.ui.display_error(str(err))

    async def _stream_output(self, result: StreamedRunResult) -> None:
        deltas = result.stream_text(delta=True)
        # Thinking covers the wait until the first chunk arrives.
        with self.ui.thinking():
            first = await anext(deltas, "")
        response = self.ui.begin_response()
        try:
            response.append(first)
            async for delta in deltas:
                response.append(delta)
        finally:
            response.finish()
