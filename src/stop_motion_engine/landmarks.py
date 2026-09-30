from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

POSE_CONNECTIONS = [
    (0, 11), (0, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (24, 26), (26, 28),
    (27, 29), (29, 31), (28, 30), (30, 32),
]


def mediapipe_available() -> bool:
    return importlib.util.find_spec("mediapipe") is not None


def _status(detected: bool, confidence: float | None = None) -> str:
    if not detected:
        return "FAILED"
    if confidence is not None and confidence < 0.5:
        return "LOW CONFIDENCE"
    return "PASS"


def _mean_visibility(points: list[dict[str, float]]) -> float:
    vals = [float(p.get("visibility", 1.0)) for p in points]
    return sum(vals) / len(vals) if vals else 0.0


def _approx_gaze(face_points: list[dict[str, float]]) -> dict[str, Any]:
    if len(face_points) < 478:
        return {"direction": "unknown", "confidence": 0.0}
    left_iris = face_points[468:473]
    right_iris = face_points[473:478]
    lx = sum(p["x"] for p in left_iris) / len(left_iris)
    rx = sum(p["x"] for p in right_iris) / len(right_iris)
    cx = (lx + rx) / 2.0
    direction = "centre"
    if cx < 0.46:
        direction = "left"
    elif cx > 0.54:
        direction = "right"
    return {"direction": direction, "confidence": 0.55, "iris_centre_x": cx}


def _approx_head(face_points: list[dict[str, float]]) -> dict[str, float]:
    if len(face_points) < 264:
        return {}
    nose = face_points[1]
    left_eye = face_points[33]
    right_eye = face_points[263]
    eye_mid_x = (left_eye["x"] + right_eye["x"]) / 2.0
    eye_mid_y = (left_eye["y"] + right_eye["y"]) / 2.0
    yaw = (nose["x"] - eye_mid_x) * 90.0
    pitch = (nose["y"] - eye_mid_y - 0.08) * 90.0
    return {"yaw": yaw, "pitch": pitch, "roll": 0.0, "method": "2d-approximation"}


class MediaPipeLandmarkPipeline:
    """Optional MediaPipe Solutions pipeline; no external .task model required."""

    def __init__(self) -> None:
        self.available = mediapipe_available()
        self._pose = self._face = self._hands = None
        if not self.available:
            return
        import mediapipe as mp
        if not hasattr(mp, "solutions"):
            self.available = False
            return
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=True, model_complexity=1,
            enable_segmentation=False, min_detection_confidence=0.5,
        )
        self._face = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True, max_num_faces=1, refine_landmarks=True,
            min_detection_confidence=0.5,
        )
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=True, max_num_hands=2, min_detection_confidence=0.5,
        )

    def close(self) -> None:
        for obj in (self._pose, self._face, self._hands):
            if obj is not None:
                obj.close()

    def extract(self, image_path: Path) -> dict[str, Any]:
        if not self.available:
            return {
                "pose": {"detected": False, "landmarks_2d": [], "confidence": 0.0},
                "face": {"detected": False, "landmarks": [], "confidence": 0.0},
                "hands": {"left": {}, "right": {}},
                "head": {}, "gaze": {},
                "status": {
                    "body_pose": "UNAVAILABLE",
                    "face": "UNAVAILABLE",
                    "left_hand": "UNAVAILABLE",
                    "right_hand": "UNAVAILABLE",
                    "reason": "MediaPipe is not installed or its Solutions API is unavailable.",
                },
            }

        import numpy as np
        rgb = np.asarray(Image.open(image_path).convert("RGB"))
        pr = self._pose.process(rgb)
        fr = self._face.process(rgb)
        hr = self._hands.process(rgb)

        pose_points: list[dict[str, float]] = []
        if pr.pose_landmarks:
            pose_points = [
                {"index": i, "x": float(p.x), "y": float(p.y), "z": float(p.z), "visibility": float(p.visibility)}
                for i, p in enumerate(pr.pose_landmarks.landmark)
            ]
        pose_conf = _mean_visibility(pose_points)

        face_points: list[dict[str, float]] = []
        if fr.multi_face_landmarks:
            face_points = [
                {"index": i, "x": float(p.x), "y": float(p.y), "z": float(p.z)}
                for i, p in enumerate(fr.multi_face_landmarks[0].landmark)
            ]

        hands: dict[str, Any] = {"left": {}, "right": {}}
        if hr.multi_hand_landmarks:
            handed = hr.multi_handedness or []
            for idx, lm in enumerate(hr.multi_hand_landmarks):
                side = "left"
                score = 0.0
                if idx < len(handed):
                    cls = handed[idx].classification[0]
                    side = str(cls.label).lower()
                    score = float(cls.score)
                hands[side] = {
                    "detected": True, "confidence": score,
                    "landmarks": [{"index": i, "x": float(p.x), "y": float(p.y), "z": float(p.z)} for i, p in enumerate(lm.landmark)],
                }

        face_conf = 1.0 if face_points else 0.0
        return {
            "pose": {"detected": bool(pose_points), "landmarks_2d": pose_points, "confidence": pose_conf},
            "face": {"detected": bool(face_points), "landmarks": face_points, "confidence": face_conf},
            "hands": hands,
            "head": _approx_head(face_points),
            "gaze": _approx_gaze(face_points),
            "status": {
                "body_pose": _status(bool(pose_points), pose_conf),
                "face": _status(bool(face_points), face_conf),
                "left_hand": _status(bool(hands.get("left", {}).get("detected")), hands.get("left", {}).get("confidence", 0.0)),
                "right_hand": _status(bool(hands.get("right", {}).get("detected")), hands.get("right", {}).get("confidence", 0.0)),
            },
        }


def draw_pose_overlay(image_path: Path, pose: dict[str, Any], output_path: Path, status: dict[str, Any] | None = None) -> Path:
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    w, h = image.size
    points = pose.get("landmarks_2d") or []
    by_idx = {int(p["index"]): p for p in points if "index" in p}
    for a, b in POSE_CONNECTIONS:
        if a in by_idx and b in by_idx:
            pa, pb = by_idx[a], by_idx[b]
            draw.line((pa["x"] * w, pa["y"] * h, pb["x"] * w, pb["y"] * h), fill="white", width=max(2, w // 300))
    for p in points:
        x, y = p["x"] * w, p["y"] * h
        r = max(2, w // 250)
        draw.ellipse((x-r, y-r, x+r, y+r), fill="white")
    if not points:
        msg = "POSE LANDMARKS UNAVAILABLE"
        if status and status.get("reason"):
            msg += "\n" + str(status["reason"])
        draw.rectangle((8, 8, min(w-8, 440), 76), fill=(0, 0, 0))
        draw.multiline_text((16, 16), msg, fill="white", spacing=4)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path
