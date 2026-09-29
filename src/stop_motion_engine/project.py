"""Project layout and reproducibility manifest."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

PROJECT_DIRS = [
    "source/frames", "identity/face", "identity/body", "analysis", "poses/source",
    "poses/target", "face", "scene", "renders/raw", "renders/accepted",
    "renders/rejected", "renders/repaired", "contact-sheets", "interpolation",
    "exports", "logs",
]


def init_project(root: Path, source: str | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for part in PROJECT_DIRS:
        (root / part).mkdir(parents=True, exist_ok=True)
    manifest = root / "manifest.json"
    if not manifest.exists():
        manifest.write_text(json.dumps({
            "schema": "stop-motion-engine.project.v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "identity": {},
            "scene": {},
            "renderer": {},
            "seeds": {},
        }, indent=2) + "\n")
    return root
