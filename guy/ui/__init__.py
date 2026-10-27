from .base import UserInterface
from .plain import PlainUserInterface
from .rich import RichUserInterface


def get_app_ui(plain: bool = True) -> UserInterface:
    if plain:
        return PlainUserInterface()
    return RichUserInterface()
