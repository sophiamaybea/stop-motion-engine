from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stop_motion_engine.lab import build_contact_sheet, generate_beat, load_beat_annotations, load_project, probe_video, save_project, validate_beat
from stop_motion_engine.lab_models import IdentityLock


def make_video(path: Path, seconds: float = 4.0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg","-y","-f","lavfi","-i",f"testsrc=size=320x240:rate=10:duration={seconds}","-pix_fmt","yuv420p",str(path)]
    subprocess.run(cmd, check=True, capture_output=True)
    return path


def make_annotations(path: Path, count: int = 21) -> Path:
    phrases = []
    for i in range(count):
        phrases.append({"id":i+1,"screen_start":i*0.15,"screen_end":i*0.15+0.1,"name":f"beat-{i+1}","sequence":"gesture","animation_note":"preserve timing"})
    path.write_text(json.dumps({"phrases":phrases}))
    return path


def test_video_ingestion_and_metadata(tmp_path: Path):
    video = make_video(tmp_path/"clip.mp4")
    meta = probe_video(video)
    assert meta["width"] == 320 and meta["height"] == 240
    assert meta["fps"] == 10.0
    assert meta["frame_count"] >= 39


def test_exactly_21_beats_and_annotation_preservation(tmp_path: Path):
    ann = make_annotations(tmp_path/"beats.json", 23)
    beats = load_beat_annotations(ann, limit=21)
    assert len(beats) == 21
    assert beats[0]["dance_semantics"]["name"] == "beat-1"
    assert beats[0]["dance_semantics"]["movement_intention"] == "preserve timing"


def test_project_roundtrip_contact_sheet_and_mock_generation(tmp_path: Path):
    video = make_video(tmp_path/"clip.mp4")
    ann = make_annotations(tmp_path/"beats.json")
    project = tmp_path/"project"
    manifest = save_project(project, video, ann, IdentityLock(face_reference="face.jpg"), beat_limit=21)
    assert manifest["beat_count"] == 21
    assert all(Path(b["source_frame"]).exists() for b in manifest["beats"])
    loaded = load_project(project)
    assert loaded["identity"]["face_reference"] == "face.jpg"
    beat = generate_beat(project, 1, "mock")
    assert beat["generation"]["ok"] is True
    assert Path(beat["generated_frame"]).exists()
    val = validate_beat(project, 1)
    assert "pose_similarity" in val and "identity_consistency" in val
    sheet = build_contact_sheet(project)
    assert sheet.exists() and sheet.stat().st_size > 0
