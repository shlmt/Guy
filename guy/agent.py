from collections.abc import Callable
from pydantic_ai import Agent, ModelSettings

from .tools import Deps


def build_agent(tools: list[Callable] | None = None) -> Agent[Deps, str]:
    return Agent(
        deps_type=Deps,
        tools=tools
    )