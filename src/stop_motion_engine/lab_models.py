from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class IdentityLock:
    face_reference: str | None = None
    body_reference: str | None = None
    profile_reference: str | None = None
    hair_reference: str | None = None
    outfit_reference: str | None = None
    embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BeatRecord:
    beat_id: int
    timestamp: float
    source_frame: str
    dance_semantics: dict[str, Any] = field(default_factory=dict)
    pose: dict[str, Any] = field(default_factory=lambda: {"detected": False, "landmarks_2d": [], "confidence": 0.0})
    face: dict[str, Any] = field(default_factory=lambda: {"detected": False, "landmarks": [], "confidence": 0.0})
    hands: dict[str, Any] = field(default_factory=lambda: {"left": {}, "right": {}})
    head: dict[str, Any] = field(default_factory=dict)
    gaze: dict[str, Any] = field(default_factory=dict)
    generated_frame: str | None = None
    validation: dict[str, Any] = field(default_factory=dict)
    detector_status: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BeatRecord":
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**fields)
