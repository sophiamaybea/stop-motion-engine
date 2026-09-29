"""MOTION_SCORE.json — the shared contract for both directions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .cells import Cell


@dataclass
class MotionScore:
    source: str
    direction: str  # forward | reverse
    fps: float
    frame_count: int
    duration_s: float
    cell_count: int
    threshold: float | None
    cells: list[Cell] = field(default_factory=list)
    energies: list[float] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "stop-motion-engine.motion_score.v1",
            "source": self.source,
            "direction": self.direction,
            "fps": self.fps,
            "frame_count": self.frame_count,
            "duration_s": self.duration_s,
            "cell_count": self.cell_count,
            "threshold": self.threshold,
            "cells": [c.to_dict() for c in self.cells],
            "energies": [round(e, 4) for e in self.energies],
            "notes": self.notes,
        }


def write_score(score: MotionScore, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(score.to_dict(), indent=2) + "\n")
    return path
