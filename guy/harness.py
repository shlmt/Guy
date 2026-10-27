from pydantic_ai import Agent, ModelSettings

from .commands import CommandContext, CommandRegistry
from .models import model_registry
from .session import SessionStore
from .tools import Deps
from .ui import UserInterface


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
        self.new_session()

    def new_session(self) -> None:
        self.session_id = self.session_store.new_id()
        self.session_history = None

    def resume_session(self, session_id: str) -> None:
        self.session_history = self.session_store.load(session_id)
        self.session_id = session_id

    async def run(self) -> None:
        while True:
            user_input = (await self.ui.get_input("User")).strip()
            if not user_input:
                continue
            if await self.commands.dispatch(user_input, self.ctx):
                continue
            await self._run_turn(user_input)

    async def _run_turn(self, user_input: str) -> None:
        try:
            result = await self.agent.run(
                user_input,
                model=model_registry.get_current_model(),
                message_history=self.session_history,
                deps=self.deps,
                model_settings=ModelSettings(temperature=0.2),
            )
            self.ui.display_message(result.output, sender="Guy")

            self.session_store.append(self.session_id, result.new_messages())
            if not self.session_history:
                self.session_store.set_title(self.session_id, user_input[:50])

            self.session_history = result.all_messages()

        except Exception as err:
            self.ui.display_error(err)
