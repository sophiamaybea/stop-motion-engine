"""Discrete motion cells — the unit both directions share.

Forward stop-motion is a sequence of holds punctuated by ticks.
Reverse engineering a video means recovering those holds and ticks
from pixel change, without needing a trained pose model.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np


@dataclass
class Cell:
    index: int
    frame_start: int
    frame_end: int
    t0: float
    t1: float
    hold_frames: int
    mean_energy: float
    peak_energy: float
    change_ratio: float
    bbox: tuple[int, int, int, int] | None
    kind: str  # hold | tick | cut

    def to_dict(self) -> dict:
        d = asdict(self)
        d["bbox"] = list(self.bbox) if self.bbox else None
        return d


def to_gray(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        return frame.astype(np.float32)
    if frame.shape[2] == 4:
        frame = frame[:, :, :3]
    r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
    return (0.299 * r + 0.587 * g + 0.114 * b).astype(np.float32)


def motion_energy(a: np.ndarray, b: np.ndarray) -> tuple[float, float, np.ndarray]:
    """Return mean abs diff, fraction of moving pixels, and abs-diff map."""
    ga, gb = to_gray(a), to_gray(b)
    if ga.shape != gb.shape:
        raise ValueError(f"frame size mismatch {ga.shape} vs {gb.shape}")
    diff = np.abs(ga - gb)
    mean = float(diff.mean())
    moving = diff > 12.0
    ratio = float(moving.mean())
    return mean, ratio, diff


def bbox_from_diff(diff: np.ndarray, min_ratio: float = 0.002) -> tuple[int, int, int, int] | None:
    mask = diff > 12.0
    if mask.mean() < min_ratio:
        return None
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def adaptive_threshold(energies: list[float]) -> float:
    arr = np.array(energies, dtype=np.float32)
    if arr.size == 0:
        return 1.0
    med = float(np.median(arr))
    p90 = float(np.percentile(arr, 90))
    floor = max(med * 2.4, float(np.percentile(arr, 60)))
    return max(1.2, min(floor, (med + p90) * 0.5 if p90 > med else floor))


def detect_cells(
    frames: Iterable[np.ndarray],
    fps: float,
    energy_override: float | None = None,
) -> tuple[list[Cell], list[float], list[float]]:
    frames = list(frames)
    if len(frames) < 2:
        raise ValueError("need at least two frames")

    energies: list[float] = []
    ratios: list[float] = []
    diffs: list[np.ndarray] = []
    for i in range(1, len(frames)):
        mean, ratio, diff = motion_energy(frames[i - 1], frames[i])
        energies.append(mean)
        ratios.append(ratio)
        diffs.append(diff)

    thresh = energy_override if energy_override is not None else adaptive_threshold(energies)

    cells: list[Cell] = []
    start = 0
    for i, energy in enumerate(energies):
        is_tick = energy >= thresh and ratios[i] >= 0.0015
        if is_tick:
            frame_end = i
            if frame_end >= start:
                peak = max(energies[start:frame_end] or [0.0])
                mean_e = float(np.mean(energies[start:frame_end] or [0.0]))
                box = bbox_from_diff(diffs[i])
                cells.append(
                    Cell(
                        index=len(cells),
                        frame_start=start,
                        frame_end=frame_end,
                        t0=start / fps,
                        t1=(frame_end + 1) / fps,
                        hold_frames=frame_end - start + 1,
                        mean_energy=mean_e,
                        peak_energy=float(peak),
                        change_ratio=ratios[i],
                        bbox=box,
                        kind="hold",
                    )
                )
            start = i + 1

    last = len(frames) - 1
    if start <= last:
        peak = max(energies[start:] or [0.0])
        mean_e = float(np.mean(energies[start:] or [0.0]))
        cells.append(
            Cell(
                index=len(cells),
                frame_start=start,
                frame_end=last,
                t0=start / fps,
                t1=(last + 1) / fps,
                hold_frames=last - start + 1,
                mean_energy=mean_e,
                peak_energy=float(peak),
                change_ratio=0.0,
                bbox=None,
                kind="hold",
            )
        )

    return cells, energies, ratios
