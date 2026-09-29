"""Pose interchange utilities for DWPose/OpenPose-compatible JSON."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

COCO18 = [
    "nose", "neck", "right_shoulder", "right_elbow", "right_wrist",
    "left_shoulder", "left_elbow", "left_wrist", "right_hip", "right_knee",
    "right_ankle", "left_hip", "left_knee", "left_ankle", "right_eye",
    "left_eye", "right_ear", "left_ear",
]


def _triples(values: list[float]) -> list[dict[str, float]]:
    return [
        {"x": float(values[i]), "y": float(values[i + 1]), "confidence": float(values[i + 2])}
        for i in range(0, len(values) - 2, 3)
    ]


def load_openpose_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    people = data.get("people") or []
    if not people:
        return {"detected": False, "body": {}, "hands": {}}
    person = people[0]
    pts = _triples(person.get("pose_keypoints_2d", []))
    body = {name: pts[i] for i, name in enumerate(COCO18) if i < len(pts)}
    return {
        "detected": True,
        "body": body,
        "hands": {
            "left": _triples(person.get("hand_left_keypoints_2d", [])),
            "right": _triples(person.get("hand_right_keypoints_2d", [])),
        },
        "face": _triples(person.get("face_keypoints_2d", [])),
    }


def pose_delta(a: dict[str, Any], b: dict[str, Any]) -> float:
    aa, bb = a.get("body", {}), b.get("body", {})
    common = set(aa) & set(bb)
    diffs = []
    for name in common:
        pa, pb = aa[name], bb[name]
        if min(pa.get("confidence", 0), pb.get("confidence", 0)) < 0.15:
            continue
        diffs.append(((pa["x"] - pb["x"]) ** 2 + (pa["y"] - pb["y"]) ** 2) ** 0.5)
    return float(np.mean(diffs)) if diffs else 0.0


def load_pose_directory(directory: Path, frame_count: int) -> list[dict[str, Any]]:
    files = sorted(directory.glob("*.json"))
    poses = [load_openpose_json(p) for p in files[:frame_count]]
    poses.extend({"detected": False, "body": {}, "hands": {}} for _ in range(frame_count - len(poses)))
    return poses
