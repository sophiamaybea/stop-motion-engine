"""Environment diagnostics for local-first performance rendering."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil


def doctor() -> dict[str, dict[str, object]]:
    rife = os.getenv("RIFE_DIR")
    return {
        "ffmpeg": {"ok": shutil.which("ffmpeg") is not None, "path": shutil.which("ffmpeg")},
        "ffprobe": {"ok": shutil.which("ffprobe") is not None, "path": shutil.which("ffprobe")},
        "mediapipe": {"ok": importlib.util.find_spec("mediapipe") is not None},
        "mcp": {"ok": importlib.util.find_spec("mcp") is not None},
        "comfyui": {"ok": bool(os.getenv("COMFYUI_URL")), "url": os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")},
        "rife": {"ok": bool(rife and Path(rife).exists()), "path": rife},
    }
