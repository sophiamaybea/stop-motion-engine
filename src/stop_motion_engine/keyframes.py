"""Adaptive keyframe selection for performance, not fixed-rate sampling."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class FrameSignal:
    frame: int
    motion: float = 0.0
    pose_delta: float = 0.0
    expression_delta: float = 0.0
    contact_event: float = 0.0
    reversal: float = 0.0


def _robust_unit(values: np.ndarray) -> np.ndarray:
    if not len(values):
        return values.astype(float)
    finite = values[np.isfinite(values)]
    if not len(finite):
        return np.zeros_like(values, dtype=float)
    lo, hi = np.quantile(finite, [0.10, 0.90])
    if hi <= lo + 1e-9:
        vmin, vmax = float(finite.min()), float(finite.max())
        if vmax <= vmin + 1e-9:
            return np.zeros_like(values, dtype=float)
        return np.clip((values - vmin) / (vmax - vmin), 0.0, 1.0)
    return np.clip((values - lo) / (hi - lo), 0.0, 1.0)


def score_signals(signals: Iterable[FrameSignal]) -> tuple[list[FrameSignal], np.ndarray]:
    rows = list(signals)
    if not rows:
        return [], np.array([], dtype=float)
    motion = _robust_unit(np.array([r.motion for r in rows], dtype=float))
    pose = _robust_unit(np.array([r.pose_delta for r in rows], dtype=float))
    expression = _robust_unit(np.array([r.expression_delta for r in rows], dtype=float))
    contacts = np.clip(np.array([r.contact_event for r in rows], dtype=float), 0, 1)
    reversal = np.clip(np.array([r.reversal for r in rows], dtype=float), 0, 1)
    score = 0.36 * motion + 0.27 * pose + 0.22 * expression + 0.08 * contacts + 0.07 * reversal
    return rows, np.clip(score, 0.0, 1.0)


def select_keyframes(
    signals: Iterable[FrameSignal],
    *,
    fps: float,
    min_spacing_s: float = 0.08,
    max_gap_s: float = 0.55,
    quantile: float = 0.72,
) -> tuple[list[int], dict[int, float]]:
    rows, scores = score_signals(signals)
    if not rows:
        return [], {}
    min_spacing = max(1, round(fps * min_spacing_s))
    max_gap = max(min_spacing + 1, round(fps * max_gap_s))
    threshold = float(np.quantile(scores, quantile)) if len(scores) > 2 else 0.0

    mandatory = {rows[0].frame, rows[-1].frame}
    for i, row in enumerate(rows):
        prev = scores[i - 1] if i else -1.0
        nxt = scores[i + 1] if i + 1 < len(scores) else -1.0
        event = row.contact_event >= 0.5 or row.reversal >= 0.5
        if event or (scores[i] >= threshold and scores[i] >= prev and scores[i] >= nxt):
            mandatory.add(row.frame)

    ordered = sorted(mandatory)
    chosen: list[int] = []
    score_by_frame = {r.frame: float(scores[i]) for i, r in enumerate(rows)}
    for frame in ordered:
        if not chosen or frame - chosen[-1] >= min_spacing or frame in (rows[0].frame, rows[-1].frame):
            chosen.append(frame)
        elif score_by_frame.get(frame, 0) > score_by_frame.get(chosen[-1], 0):
            chosen[-1] = frame

    all_frames = [r.frame for r in rows]
    while True:
        inserted = False
        out: list[int] = [chosen[0]]
        for a, b in zip(chosen, chosen[1:]):
            if b - a > max_gap:
                candidates = [f for f in all_frames if a + min_spacing <= f <= b - min_spacing]
                target = max(candidates, key=lambda f: score_by_frame.get(f, 0.0)) if candidates else (a + b) // 2
                out.append(target)
                inserted = True
            out.append(b)
        chosen = sorted(set(out))
        if not inserted:
            break

    return chosen, score_by_frame
