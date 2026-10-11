from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Deps:
    work_dir: Path

    def resolve_work_path(self, file: str) -> Path:
        path = (self.work_dir / file).resolve()
        if not path.is_relative_to(self.work_dir.resolve()):
            raise ValueError(f"path escapes work dir: {file}")
        return path