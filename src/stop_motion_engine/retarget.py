"""Proportion-aware 2D skeletal retargeting."""
from __future__ import annotations

from dataclasses import dataclass, field
import math

BONES = [
    ("neck", "right_shoulder"), ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"),
    ("neck", "left_shoulder"), ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
    ("right_hip", "right_knee"), ("right_knee", "right_ankle"),
    ("left_hip", "left_knee"), ("left_knee", "left_ankle"),
]


@dataclass
class SkeletonProfile:
    bone_lengths: dict[str, float] = field(default_factory=dict)

    @staticmethod
    def key(a: str, b: str) -> str:
        return f"{a}>{b}"


def _distance(a: dict[str, float], b: dict[str, float]) -> float:
    return math.hypot(float(b["x"]) - float(a["x"]), float(b["y"]) - float(a["y"]))


def infer_profile(body: dict[str, dict[str, float]]) -> SkeletonProfile:
    lengths: dict[str, float] = {}
    torso = 0.0
    if "neck" in body and "left_hip" in body and "right_hip" in body:
        hip = {"x": (body["left_hip"]["x"] + body["right_hip"]["x"]) / 2,
               "y": (body["left_hip"]["y"] + body["right_hip"]["y"]) / 2}
        torso = _distance(body["neck"], hip)
    scale = torso or 1.0
    for a, b in BONES:
        if a in body and b in body:
            lengths[SkeletonProfile.key(a, b)] = _distance(body[a], body[b]) / scale
    return SkeletonProfile(lengths)


def retarget_named_pose(
    source: dict[str, dict[str, float]],
    target: SkeletonProfile,
    *,
    torso_scale: float | None = None,
) -> dict[str, dict[str, float]]:
    out = {k: dict(v) for k, v in source.items()}
    if torso_scale is None:
        if "neck" in source and "left_hip" in source and "right_hip" in source:
            hip = {"x": (source["left_hip"]["x"] + source["right_hip"]["x"]) / 2,
                   "y": (source["left_hip"]["y"] + source["right_hip"]["y"]) / 2}
            torso_scale = _distance(source["neck"], hip)
        else:
            torso_scale = 1.0
    for parent, child in BONES:
        if parent not in out or child not in source:
            continue
        p = out[parent]
        src_parent, src_child = source[parent], source[child]
        dx = float(src_child["x"]) - float(src_parent["x"])
        dy = float(src_child["y"]) - float(src_parent["y"])
        length = math.hypot(dx, dy)
        if length < 1e-9:
            continue
        desired = target.bone_lengths.get(SkeletonProfile.key(parent, child))
        if desired is None:
            continue
        desired_px = desired * torso_scale
        out[child] = {
            **source[child],
            "x": float(p["x"]) + dx / length * desired_px,
            "y": float(p["y"]) + dy / length * desired_px,
        }
    return out
