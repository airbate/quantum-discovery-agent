from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


class ArtifactStore:
    def __init__(self, root: str | Path = "artifacts"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write_json(self, run_id: str, round_id: str, name: str, payload: Any) -> str:
        target_dir = self.root / run_id / round_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{name}.json"
        temporary = target.with_suffix(".json.tmp")
        encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        with temporary.open("wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(target)
        digest = hashlib.sha256(encoded).hexdigest()[:16]
        return f"{run_id}/{round_id}/{name}.json#{digest}"

    def read_json(self, artifact_id: str) -> Any:
        path = self.root / artifact_id.split("#", 1)[0]
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
