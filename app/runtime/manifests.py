from __future__ import annotations

import hashlib
import json
from typing import Any


def config_hash(config: Any) -> str:
    if hasattr(config, "model_dump"):
        config = config.model_dump(mode="json")
    payload = json.dumps(config, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
