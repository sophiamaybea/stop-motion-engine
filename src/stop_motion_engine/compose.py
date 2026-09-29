"""Forward path — discrete stills become a stop-motion clip."""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
from PIL import Image


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def list_frames(folder: Path) -> list[Path]:
    files = [p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS]
    return sorted(files, key=lambda p: p.name)


def load_rgb(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.array(img)


def compose_from_frames(
    frames_dir: Path,
    output: Path,
    fps: float = 12.0,
    ffmpeg: str = "ffmpeg",
) -> Path:
    frames = list_frames(frames_dir)
    if not frames:
        raise FileNotFoundError(f"no images in {frames_dir}")
    output.parent.mkdir(parents=True, exist_ok=True)
    list_file = output.parent / f"{output.stem}_concat.txt"
    lines = []
    duration = 1.0 / fps
    for p in frames:
        lines.append(f"file '{p.resolve()}'")
        lines.append(f"duration {duration:.6f}")
    lines.append(f"file '{frames[-1].resolve()}'")
    list_file.write_text("\n".join(lines) + "\n")
    cmd = [
        ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-vsync", "vfr", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:])
    return output


def write_onion_sheet(
    frames_dir: Path,
    output: Path,
    previous_alpha: float = 0.35,
    columns: int = 6,
) -> Path:
    paths = list_frames(frames_dir)
    if not paths:
        raise FileNotFoundError(f"no images in {frames_dir}")
    images = [Image.open(p).convert("RGBA") for p in paths]
    w, h = images[0].size
    onions: list[Image.Image] = []
    prev = None
    for img in images:
        if prev is None:
            onions.append(img.convert("RGB"))
        else:
            ghost = prev.copy()
            ghost.putalpha(int(255 * previous_alpha))
            base = img.convert("RGBA")
            composed = Image.alpha_composite(base, ghost)
            onions.append(composed.convert("RGB"))
        prev = img
    rows = (len(onions) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * w, rows * h), (12, 12, 14))
    for i, frame in enumerate(onions):
        r, c = divmod(i, columns)
        if frame.size != (w, h):
            frame = frame.resize((w, h))
        sheet.paste(frame, (c * w, r * h))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return output
