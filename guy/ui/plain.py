from typing import List

from .base import UserInterface


class PlainUserInterface(UserInterface):
    """Basic user interface using Python standard print and input functions."""

    def display_message(self, message: str, sender: str = None) -> None:
        if sender:
            print(f"{sender}: {message}")
        else:
            print(message)

    def get_input(self, prompt: str) -> str:
        return input(f"{prompt} ")

    def display_warning(self, warning_message: str) -> None:
        print(f"WARNING: {warning_message}")

    def display_error(self, error_message: str) -> None:
        print(f"ERROR: {error_message}")

    def display_success(self, success_message: str) -> None:
        print(f"SUCCESS: {success_message}")

    def ask_permission(self, prompt: str) -> bool:
        response = input(f"{prompt} (y/n): ").strip().lower()
        return response in ("y", "yes")

    def select_option(self, prompt: str, options: List[str]) -> int:
        print(prompt)
        for idx, option in enumerate(options, 1):
            print(f"  {idx}. {option}")
        while True:
            choice = input(f"Select option (1-{len(options)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                return int(choice) - 1
            print("Invalid selection. Try again.")
