"""Video -> structured performance analysis."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .cells import adaptive_threshold, detect_cells
from .face import expression_delta, extract_face_performance
from .keyframes import FrameSignal, select_keyframes
from .performance import HeadPose, MovementFlags, PerformanceFrame, PerformanceTrack
from .pose import load_pose_directory, pose_delta
from .project import init_project
from .reverse import extract_frames, load_frames, probe_fps, write_cell_stills
from .score import MotionScore, write_score


def analyse_performance(
    source: Path,
    project: Path,
    *,
    face_model: Path | None = None,
    pose_json_dir: Path | None = None,
) -> dict[str, Path]:
    init_project(project, str(source))
    frames_dir = project / "source" / "frames"
    paths = sorted(frames_dir.glob("f_*.png"))
    if not paths:
        paths = extract_frames(source, frames_dir)
    fps = probe_fps(source)
    arrays = load_frames(paths)
    cells, energies, _ = detect_cells(arrays, fps=fps)
    motion = [0.0] + [float(x) for x in energies]
    write_cell_stills(cells, paths, project / "analysis" / "cells")
    threshold = adaptive_threshold(energies)
    write_score(MotionScore(
        source=str(source), direction="reverse", fps=fps,
        frame_count=len(arrays), duration_s=len(arrays) / fps,
        cell_count=len(cells), threshold=threshold,
        cells=cells, energies=energies,
        notes=["Motion score generated as one signal inside the performance analyser."],
    ), project / "analysis" / "MOTION_SCORE.json")

    faces: list[dict[str, Any]] = [{"detected": False, "blendshapes": {}, "head": {}} for _ in paths]
    if face_model is not None:
        faces = extract_face_performance(paths, face_model)
    poses: list[dict[str, Any]] = [{"detected": False, "body": {}, "hands": {}} for _ in paths]
    if pose_json_dir is not None:
        poses = load_pose_directory(pose_json_dir, len(paths))

    signals: list[FrameSignal] = []
    previous_face: dict[str, float] = {}
    previous_pose: dict[str, Any] = {}
    for i in range(len(paths)):
        current_face = faces[i].get("blendshapes", {})
        current_pose = poses[i]
        ed = expression_delta(previous_face, current_face) if i else 0.0
        pd = pose_delta(previous_pose, current_pose) if i else 0.0
        signals.append(FrameSignal(frame=i, motion=motion[i], pose_delta=pd, expression_delta=ed))
        previous_face, previous_pose = current_face, current_pose

    keyframes, importance = select_keyframes(signals, fps=fps)
    performance_frames: list[PerformanceFrame] = []
    for i in keyframes:
        face = faces[i]
        h = face.get("head") or {}
        performance_frames.append(PerformanceFrame(
            source_frame=i,
            time_seconds=i / fps,
            importance=importance.get(i, 0.0),
            body=poses[i].get("body", {}),
            hands=poses[i].get("hands", {}),
            head=HeadPose(yaw=float(h.get("yaw", 0)), pitch=float(h.get("pitch", 0)), roll=float(h.get("roll", 0))),
            face={k: v for k, v in face.items() if k != "head"},
            movement=MovementFlags(hold=motion[i] <= threshold),
        ))

    track = PerformanceTrack(
        source=str(source), fps=fps, frame_count=len(paths), frames=performance_frames,
        metadata={
            "selected_keyframes": len(keyframes),
            "face_model": str(face_model) if face_model else None,
            "pose_source": str(pose_json_dir) if pose_json_dir else None,
        },
    )
    performance_path = track.write(project / "analysis" / "PERFORMANCE.json")
    keyframes_path = project / "analysis" / "KEYFRAMES.json"
    keyframes_path.write_text(json.dumps({
        "schema": "stop-motion-engine.keyframes.v1",
        "fps": fps,
        "keyframes": [{"frame": f, "time": f / fps, "importance": importance.get(f, 0.0)} for f in keyframes],
    }, indent=2) + "\n")
    return {
        "performance": performance_path,
        "keyframes": keyframes_path,
        "motion": project / "analysis" / "MOTION_SCORE.json",
    }
