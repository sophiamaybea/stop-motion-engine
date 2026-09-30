from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import socket


def _tcp(host: str, port: int, timeout: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def system_check() -> dict[str, dict[str, object]]:
    comfy_url = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
    comfy_ok = _tcp("127.0.0.1", 8188) if comfy_url.startswith("http://127.0.0.1:8188") else bool(os.getenv("COMFYUI_URL"))
    mp = importlib.util.find_spec("mediapipe") is not None
    return {
        "FFmpeg": {"ok": shutil.which("ffmpeg") is not None, "detail": shutil.which("ffmpeg")},
        "FFprobe": {"ok": shutil.which("ffprobe") is not None, "detail": shutil.which("ffprobe")},
        "Pose detector": {"ok": mp, "detail": "MediaPipe Pose" if mp else "install performance extra / use Python 3.11-3.12"},
        "Face detector": {"ok": mp, "detail": "MediaPipe FaceMesh" if mp else "install performance extra / use Python 3.11-3.12"},
        "Hand detector": {"ok": mp, "detail": "MediaPipe Hands" if mp else "install performance extra / use Python 3.11-3.12"},
        "GPU": {"ok": False, "detail": "not required for structural mode; runtime detection delegated to renderer backend"},
        "SMPL": {"ok": importlib.util.find_spec("smplx") is not None, "detail": "optional second-stage adapter"},
        "Comfy endpoint": {"ok": comfy_ok, "detail": comfy_url},
        "Identity model": {"ok": bool(os.getenv("IDENTITY_MODEL")), "detail": os.getenv("IDENTITY_MODEL", "not configured")},
        "RIFE": {"ok": bool(os.getenv("RIFE_DIR") and Path(os.environ["RIFE_DIR"]).exists()), "detail": os.getenv("RIFE_DIR", "not configured")},
    }
