"""Facial-performance extraction via the official MediaPipe Face Landmarker."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np


def _rotation_to_euler(matrix: list[list[float]] | np.ndarray) -> dict[str, float]:
    r = np.asarray(matrix, dtype=float)[:3, :3]
    sy = math.sqrt(r[0, 0] ** 2 + r[1, 0] ** 2)
    singular = sy < 1e-6
    if not singular:
        x = math.atan2(r[2, 1], r[2, 2])
        y = math.atan2(-r[2, 0], sy)
        z = math.atan2(r[1, 0], r[0, 0])
    else:
        x = math.atan2(-r[1, 2], r[1, 1])
        y = math.atan2(-r[2, 0], sy)
        z = 0.0
    return {"pitch": math.degrees(x), "yaw": math.degrees(y), "roll": math.degrees(z)}


def expression_delta(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) | set(b)
    if not keys:
        return 0.0
    return float(sum(abs(float(a.get(k, 0.0)) - float(b.get(k, 0.0))) for k in keys) / len(keys))


def extract_face_performance(frame_paths: list[Path], model_path: Path) -> list[dict[str, Any]]:
    try:
        import mediapipe as mp
    except ImportError as exc:
        raise RuntimeError("MediaPipe is not installed. Install the 'performance' extra.") from exc

    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        num_faces=1,
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=True,
    )
    output: list[dict[str, Any]] = []
    with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
        for path in frame_paths:
            result = landmarker.detect(mp.Image.create_from_file(str(path)))
            if not result.face_landmarks:
                output.append({"detected": False, "blendshapes": {}, "landmarks": [], "head": {}})
                continue
            landmarks = [{"x": float(p.x), "y": float(p.y), "z": float(p.z)} for p in result.face_landmarks[0]]
            shapes: dict[str, float] = {}
            if result.face_blendshapes:
                for c in result.face_blendshapes[0]:
                    name = getattr(c, "category_name", None) or getattr(c, "display_name", "")
                    if name:
                        shapes[str(name)] = float(c.score)
            matrix, head = [], {}
            if result.facial_transformation_matrixes:
                m = np.asarray(result.facial_transformation_matrixes[0], dtype=float)
                matrix, head = m.tolist(), _rotation_to_euler(m)
            output.append({
                "detected": True,
                "blendshapes": shapes,
                "landmarks": landmarks,
                "transformation_matrix": matrix,
                "head": head,
            })
    return output
