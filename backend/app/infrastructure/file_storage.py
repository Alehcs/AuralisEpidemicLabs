"""Local file storage boundary for future runs and snapshots."""

import json
from pathlib import Path
from typing import Any


class FileStorage:
    """Persist JSON artifacts locally until durable storage is introduced."""

    def __init__(self, base_directory: Path | str) -> None:
        self.base_directory = Path(base_directory)

    def write_json(self, relative_path: str, payload: dict[str, Any]) -> Path:
        """Write an artifact below the configured output directory."""

        path = (self.base_directory / relative_path).resolve()
        base = self.base_directory.resolve()
        if base not in path.parents:
            raise ValueError("Output path must remain inside the storage directory")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path
