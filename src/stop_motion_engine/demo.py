"""Generate a known stop-motion, compose it, reverse it, report the round trip."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .compose import compose_from_frames
from .reverse import reverse_video


def paint_cell(size: tuple[int, int], x: int, y: int, label: str) -> Image.Image:
    img = Image.new("RGB", size, (24, 26, 32))
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 40, size[0] - 40, size[1] - 40], outline=(60, 64, 80), width=2)
    draw.rectangle([x, y, x + 48, y + 48], fill=(232, 92, 120))
    draw.text((16, 12), label, fill=(200, 204, 214))
    return img


def write_synthetic(dest: Path, shots: int = 12, hold: int = 2) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    w, h = 320, 240
    n = 0
    for i in range(shots):
        x = 48 + i * 16
        y = 80 + int(40 * np.sin(i / 2.2))
        frame = paint_cell((w, h), x, y, f"shot {i:02d}")
        for _ in range(hold):
            frame.save(dest / f"{n:04d}.png")
            n += 1
    return dest


def run_demo(out: Path) -> str:
    frames = write_synthetic(out / "stills")
    video = compose_from_frames(frames, out / "forward.mp4", fps=12.0)
    score = reverse_video(video, out / "reverse")
    return (
        f"demo wrote {video}\n"
        f"expected_shots=12 recovered_cells={score.cell_count} "
        f"frames={score.frame_count} threshold={score.threshold:.3f}\n"
        f"score={out / 'reverse' / 'MOTION_SCORE.json'}"
    )
