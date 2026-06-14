"""Confined local JSON storage for exports and experiment reports."""

import json
from pathlib import Path
from typing import Any, Iterable


class FileStorage:
    """Read and write artifacts without allowing paths outside one root."""

    def __init__(self, base_directory: Path | str) -> None:
        self.base_directory = Path(base_directory).resolve()

    def resolve(self, relative_path: str) -> Path:
        path = (self.base_directory / relative_path).resolve()
        if path != self.base_directory and self.base_directory not in path.parents:
            raise ValueError("Path must remain inside the storage directory")
        return path

    def write_json(self, relative_path: str, payload: Any) -> Path:
        path = self.resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def write_jsonl(self, relative_path: str, rows: Iterable[dict[str, Any]]) -> Path:
        path = self.resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
        path.write_text(content, encoding="utf-8")
        return path

    def read_json(self, relative_path: str) -> Any:
        return json.loads(self.resolve(relative_path).read_text(encoding="utf-8"))

    def read_jsonl(self, relative_path: str) -> list[dict[str, Any]]:
        path = self.resolve(relative_path)
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
