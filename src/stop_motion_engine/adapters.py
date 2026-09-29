"""Local renderer/interpolator adapters. No paid API is required."""
from __future__ import annotations

import json
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any


class ComfyUIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8188"):
        self.base_url = base_url.rstrip("/")

    def _json(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST" if payload is not None else "GET",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())

    def queue_workflow(self, workflow: dict[str, Any], client_id: str = "performance-film") -> str:
        result = self._json("/prompt", {"prompt": workflow, "client_id": client_id})
        return str(result["prompt_id"])

    def wait(self, prompt_id: str, timeout_s: float = 600, poll_s: float = 1.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            history = self._json(f"/history/{prompt_id}")
            if prompt_id in history:
                return history[prompt_id]
            time.sleep(poll_s)
        raise TimeoutError(f"ComfyUI prompt {prompt_id} did not finish within {timeout_s}s")


def run_rife(
    source: Path,
    output_video: Path,
    rife_dir: Path,
    *,
    multi: int = 4,
    fps: float | None = None,
    scale: float = 1.0,
    python: str = "python",
) -> Path:
    output_video.parent.mkdir(parents=True, exist_ok=True)
    script = rife_dir / "inference_video.py"
    if not script.exists():
        raise FileNotFoundError(f"Practical-RIFE inference_video.py not found under {rife_dir}")
    cmd = [python, str(script), f"--multi={int(multi)}", f"--output={output_video}", f"--scale={scale}"]
    cmd.append(f"--img={source}" if source.is_dir() else f"--video={source}")
    if fps is not None:
        cmd.append(f"--fps={fps}")
    proc = subprocess.run(cmd, cwd=rife_dir, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-3000:])
    if not output_video.exists():
        raise RuntimeError("Practical-RIFE completed but did not create the requested output")
    return output_video


def assemble_frames(frames_dir: Path, output: Path, fps: float = 12.0, ffmpeg: str = "ffmpeg") -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    frames = sorted(frames_dir.glob("*.png"))
    if not frames:
        raise ValueError(f"No PNG frames in {frames_dir}")
    concat = output.parent / f".{output.stem}.frames.txt"
    duration = 1.0 / fps
    lines = []
    for frame in frames:
        safe = str(frame.resolve()).replace("'", "'\\''")
        lines.extend([f"file '{safe}'", f"duration {duration:.10f}"])
    safe = str(frames[-1].resolve()).replace("'", "'\\''")
    lines.append(f"file '{safe}'")
    concat.write_text("\n".join(lines) + "\n")
    cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
           "-vsync", "vfr", "-pix_fmt", "yuv420p", str(output)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    concat.unlink(missing_ok=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:])
    return output
