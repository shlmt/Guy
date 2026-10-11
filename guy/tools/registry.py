from collections.abc import Callable

from .base import ToolSpec


class ToolsRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}


    def register(self, func: Callable, *, group: str = "", mutates: bool = False, dangerous: bool = False) -> None:
        spec = ToolSpec(func, group, mutates, dangerous)
        if spec.name in self._tools:
            raise ValueError(f"duplicate tool: {spec.name}")
        self._tools[spec.name] = spec


    def select(
        self, *, groups: set[str] | None = None, mutates: bool | None = None
    ) -> list[Callable]:
        return [
            t.func
            for t in self._tools.values()
            if (groups is None or t.group in groups)
            and (mutates is None or t.mutates == mutates)
        ]