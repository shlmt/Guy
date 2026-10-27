from .base import (
    Command,
    CommandContext,
    CommandError,
    CommandHarness,
    Completer,
    Handler,
    ParsedLine,
)
from .completion import CommandCompletionSource
from .parsing import parse
from .registry import CommandRegistry

command_registry = CommandRegistry()

# Registered here, like tools_registry. Importing a domain's COMMANDS is the registration.
from .app_commands import COMMANDS as APP_COMMANDS
from ..session.commands import COMMANDS as SESSION_COMMANDS

for _command in (*APP_COMMANDS, *SESSION_COMMANDS):
    command_registry.register(_command)
