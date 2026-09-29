"""Canonical data contracts for performance transfer.

This module deliberately separates stable identity/scene information from changing
performance information. It has no model dependencies and is safe to import in
CLI, MCP and tests.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass
class HeadPose:
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0


@dataclass
class MovementFlags:
    direction_change: bool = False
    pose_extreme: bool = False
    impact: bool = False
    airborne: bool = False
    floor_contact: bool = False
    transition: bool = False
    hold: bool = False
    reversal: bool = False


@dataclass
class PerformanceFrame:
    source_frame: int
    time_seconds: float
    importance: float = 0.0
    body: dict[str, Any] = field(default_factory=dict)
    hands: dict[str, Any] = field(default_factory=dict)
    head: HeadPose = field(default_factory=HeadPose)
    face: dict[str, Any] = field(default_factory=dict)
    movement: MovementFlags = field(default_factory=MovementFlags)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceTrack:
    source: str
    fps: float
    frame_count: int
    frames: list[PerformanceFrame]
    schema: str = "stop-motion-engine.performance.v1"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source": self.source,
            "fps": self.fps,
            "frame_count": self.frame_count,
            "metadata": self.metadata,
            "frames": [f.to_dict() for f in self.frames],
        }

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n")
        return path
