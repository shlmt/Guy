from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolSpec:
    func: Callable
    group: str = ""
    mutates: bool = False
    dangerous: bool = False

    @property
    def name(self) -> str:
        return self.func.__name__