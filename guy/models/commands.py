from ..commands.base import (
    Command,
    CommandContext,
    CommandError,
    ParsedLine,
    Suggestion,
)
from ..config import config
from . import model_registry


def _model_candidates(ctx: CommandContext, parsed: ParsedLine) -> list[Suggestion]:
    if not parsed.args:
        # User typed "/model " or "/model <partial>"
        current = [Suggestion("current", "current", "show active model")]
        providers = [
            Suggestion(p, f"provider: {p}", "configure provider")
            for p in model_registry.get_providers()
        ]
        models = [
            Suggestion(m, f"model: {m}", "switch model")
            for m in model_registry.list_available_models()
        ]
        return current + models + providers

    first = parsed.args[0].lower()
    if first in model_registry.get_providers() and len(parsed.args) == 1:
        # User typed "/model <provider> " -> suggest subcommands
        return [
            Suggestion("set-api-key", "set-api-key <key>", "Store API key in config"),
            Suggestion("remove-api-key", "remove-api-key", "Delete API key from config"),
        ]

    return []


async def _model_command(ctx: CommandContext, args: tuple[str, ...]) -> None:
    if not args:
        # Interactive selection if available, or error / info
        available = model_registry.list_available_models()
        if not available:
            raise CommandError("no models available")

        # Pre-select current active model if present
        current = model_registry.active_model_spec
        default_idx = available.index(current) if current in available else 0
        prompt_options = [f"{m} (active)" if m == current else m for m in available]
        chosen_idx = await ctx.ui.select_option("Select model:", prompt_options)
        if chosen_idx is None:
            return

        chosen_model = available[chosen_idx]
        model_registry.set_active_model(chosen_model)
        config.default_model = chosen_model
        ctx.ui.set_status(model=chosen_model)
        ctx.ui.display_success(f"Active model set to {chosen_model}")
        return

    first = args[0]

    if first.lower() == "current":
        if len(args) != 1:
            raise CommandError("usage: /model current")
        ctx.ui.display_message(f"Active model: {model_registry.active_model_spec}")
        return

    # Check if this is a provider API key command:
    # /model <provider> set-api-key <key>
    # /model <provider> remove-api-key (or remove api key)
    providers = model_registry.get_providers()
    if first.lower() in providers:
        provider = first.lower()
        sub_args = args[1:]
        if not sub_args:
            raise CommandError(
                f"usage: /model {provider} set-api-key <key> | /model {provider} remove-api-key"
            )

        action = sub_args[0].lower()
        if action == "set-api-key":
            if len(sub_args) != 2:
                raise CommandError(f"usage: /model {provider} set-api-key <key>")
            api_key = sub_args[1]
            config.set_api_key(provider, api_key)
            ctx.ui.display_success(f"API key for '{provider}' updated successfully")
            return

        if action in ("remove-api-key", "remove"):
            # Supports both /model gemini remove-api-key and /model gemini remove api key
            if action == "remove":
                # Check for "api key" after "remove"
                rest = [a.lower() for a in sub_args[1:]]
                if rest and rest != ["api", "key"] and rest != ["api-key"]:
                    raise CommandError(
                        f"usage: /model {provider} remove-api-key (or /model {provider} remove api key)"
                    )
            removed = config.remove_api_key(provider)
            if removed:
                ctx.ui.display_success(f"API key for '{provider}' removed")
            else:
                ctx.ui.display_warning(f"No custom API key was saved for '{provider}'")
            return

        raise CommandError(f"unknown provider action: {action}")

    # Otherwise, switch directly to the specified model spec
    if len(args) != 1:
        raise CommandError("usage: /model [model_name] or /model <provider> set-api-key <key>")

    model_spec = first
    try:
        model_registry.set_active_model(model_spec)
        config.default_model = model_spec
        ctx.ui.set_status(model=model_spec)
        ctx.ui.display_success(f"Active model set to {model_spec}")
    except ValueError as err:
        raise CommandError(str(err)) from err


COMMANDS = (
    Command(
        "model",
        _model_command,
        "Switch model or manage provider API keys",
        "/model [model] | /model <provider> set-api-key <key> | /model <provider> remove-api-key",
        _model_candidates,
    ),
)
