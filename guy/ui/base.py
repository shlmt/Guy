from abc import ABC, abstractmethod
from typing import List


class UserInterface(ABC):
    """Abstract base class defining the contract for user interface implementations."""

    @abstractmethod
    def display_message(self, message: str, sender: str = None) -> None:
        pass

    @abstractmethod
    def get_input(self, prompt: str) -> str:
        pass

    @abstractmethod
    def display_warning(self, warn_message: str) -> None:
        pass

    @abstractmethod
    def display_error(self, error_message: str) -> None:
        pass

    @abstractmethod
    def display_success(self, success_message: str) -> None:
        pass

    @abstractmethod
    def ask_permission(self, prompt: str) -> bool:
        """Ask for user permission (yes/no). Returns True for positive confirmation."""
        pass

    @abstractmethod
    def select_option(self, prompt: str, options: List[str]) -> int:
        """Present a list of options to the user and return the selected index."""
        pass
