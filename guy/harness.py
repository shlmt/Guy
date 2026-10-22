from pydantic_ai import ModelSettings

from .paths import WORK_DIR
from .models import model_registry
from .session import SessionStore
from .ui import app_ui
from .agent import build_agent
from .tools import tools_registry, Deps


async def main():
    work_deps = Deps(WORK_DIR)

    tools = tools_registry.select()
    agent = build_agent(tools)

    session_store = SessionStore()
    session_id = session_store.new_id()
    session_history = None

    while True:
        user_input = app_ui.get_input("\nUser > ").strip()
        if not user_input:
            continue

        current_model = model_registry.get_current_model()

        try:
            result = await agent.run(
                user_input,
                model=current_model,
                message_history=session_history,
                deps=work_deps,
                model_settings=ModelSettings(temperature=0.2),
            )
            app_ui.display_message(result.output, sender="Guy")

            session_store.append(session_id, result.new_messages())
            if not session_history:
                session_store.set_title(session_id, user_input[:50])

            session_history = result.all_messages()

        except Exception as err:
            app_ui.display_error(err)
