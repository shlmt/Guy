from pydantic_ai import Agent, ModelSettings

from .models import model_registry
from .ui import app_ui


async def main():
    agent = Agent()
    session_history = None

    while True:
        user_input = app_ui.get_input("\nUser > ").strip()
        if not user_input:
            continue

        current_model = model_registry.get_current_model()

        try:
            result = await agent.run(user_input, model=current_model, message_history=session_history, model_settings=ModelSettings(temperature=0.2))
            session_history = result.all_messages()
            app_ui.display_message(result.output, sender="Guy") 
        
        except Exception as err:
            app_ui.display_error(err)