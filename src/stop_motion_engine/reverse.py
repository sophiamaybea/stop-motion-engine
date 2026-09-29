"""Reverse path — a video becomes the stop-motion cells that would have made it."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from .cells import adaptive_threshold, detect_cells
from .compose import IMAGE_EXTS
from .score import MotionScore, write_score


def probe_fps(video: Path, ffmpeg: str = "ffprobe") -> float:
    cmd = [
        ffmpeg, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate", "-of", "json", str(video),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-1000:])
    data = json.loads(proc.stdout)
    rate = data["streams"][0]["r_frame_rate"]
    num, den = rate.split("/")
    fps = float(num) / float(den)
    if fps <= 0:
        raise RuntimeError(f"bad fps {rate}")
    return fps


def extract_frames(video: Path, dest: Path, ffmpeg: str = "ffmpeg") -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    pattern = dest / "f_%05d.png"
    cmd = [ffmpeg, "-y", "-i", str(video), "-vsync", "0", str(pattern)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:])
    return sorted(dest.glob("f_*.png"))


def load_frames(paths: list[Path]):
    out = []
    for p in paths:
        img = Image.open(p).convert("RGB")
        out.append(__import__("numpy").array(img))
    return out


def write_cell_stills(cells, frame_paths: list[Path], dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    written = []
    for cell in cells:
        src = frame_paths[cell.frame_start]
        target = dest / f"cell_{cell.index:04d}_f{cell.frame_start:05d}.png"
        shutil.copy2(src, target)
        written.append(target)
    return written


def reverse_video(
    video: Path,
    out_dir: Path,
    fps_override: float | None = None,
    energy_override: float | None = None,
    keep_all_frames: bool = False,
) -> MotionScore:
    out_dir.mkdir(parents=True, exist_ok=True)
    fps = fps_override if fps_override is not None else probe_fps(video)
    work = Path(tempfile.mkdtemp(prefix="sme-rev-"))
    try:
        frame_paths = extract_frames(video, work / "frames")
        if keep_all_frames:
            kept = out_dir / "frames"
            kept.mkdir(exist_ok=True)
            for p in frame_paths:
                shutil.copy2(p, kept / p.name)
            frame_paths_for_cells = sorted((out_dir / "frames").glob("f_*.png"))
        else:
            frame_paths_for_cells = frame_paths
        arrays = load_frames(frame_paths)
        cells, energies, _ratios = detect_cells(arrays, fps=fps, energy_override=energy_override)
        write_cell_stills(cells, frame_paths_for_cells, out_dir / "cells")
        thresh = energy_override if energy_override is not None else adaptive_threshold(energies)
        score = MotionScore(
            source=str(video),
            direction="reverse",
            fps=fps,
            frame_count=len(arrays),
            duration_s=len(arrays) / fps,
            cell_count=len(cells),
            threshold=thresh,
            cells=cells,
            energies=energies,
            notes=[
                "A cell is a hold: frames that did not tick.",
                "A tick is a jump in mean-abs luminance above an adaptive floor.",
                "bbox is the changed region on the tick into the next cell.",
            ],
        )
        write_score(score, out_dir / "MOTION_SCORE.json")
        return score
    finally:
        shutil.rmtree(work, ignore_errors=True)


def reverse_frame_folder(
    frames_dir: Path,
    out_dir: Path,
    fps: float = 12.0,
    energy_override: float | None = None,
) -> MotionScore:
    paths = sorted(p for p in frames_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    arrays = load_frames(paths)
    cells, energies, _ = detect_cells(arrays, fps=fps, energy_override=energy_override)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_cell_stills(cells, paths, out_dir / "cells")
    thresh = energy_override if energy_override is not None else adaptive_threshold(energies)
    score = MotionScore(
        source=str(frames_dir),
        direction="reverse",
        fps=fps,
        frame_count=len(arrays),
        duration_s=len(arrays) / fps,
        cell_count=len(cells),
        threshold=thresh,
        cells=cells,
        energies=energies,
        notes=["Analyzed from a still sequence rather than a video container."],
    )
    write_score(score, out_dir / "MOTION_SCORE.json")
    return score
