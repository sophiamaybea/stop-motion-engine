from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from .generation import get_generator
from .lab_models import BeatRecord, IdentityLock
from .landmarks import MediaPipeLandmarkPipeline, draw_pose_overlay


def probe_video(video: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration",
        "-show_entries", "format=duration", "-of", "json", str(video),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:])
    data = json.loads(proc.stdout)
    stream = (data.get("streams") or [{}])[0]
    rate = stream.get("r_frame_rate") or "0/1"
    try:
        a, b = rate.split("/")
        fps = float(a) / float(b) if float(b) else 0.0
    except Exception:
        fps = 0.0
    duration = float(stream.get("duration") or data.get("format", {}).get("duration") or 0.0)
    frame_count = int(stream.get("nb_frames") or round(duration * fps)) if fps else int(stream.get("nb_frames") or 0)
    return {
        "duration": duration, "fps": fps, "frame_count": frame_count,
        "width": int(stream.get("width") or 0), "height": int(stream.get("height") or 0),
    }


def load_beat_annotations(path: Path, limit: int = 21) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        rows = data
    elif "beats" in data:
        rows = data["beats"]
    elif "phrases" in data:
        rows = []
        for p in data["phrases"]:
            start = float(p.get("screen_start", p.get("start", 0)))
            end = float(p.get("screen_end", p.get("end", start)))
            rows.append({
                "beat_id": int(p.get("id", len(rows)+1)),
                "timestamp": (start + end) / 2.0,
                "dance_semantics": {
                    "name": p.get("name"),
                    "support": p.get("support", "annotate/review"),
                    "free_leg": p.get("free_leg", "annotate/review"),
                    "gesture": p.get("sequence", ""),
                    "arms": p.get("arms", "derive from source + annotation"),
                    "torso": p.get("torso", p.get("animation_note", "")),
                    "head": p.get("head", "derive from source + annotation"),
                    "gaze": p.get("gaze", "derive from source + annotation"),
                    "expression": p.get("expression", "derive from source + annotation"),
                    "movement_intention": p.get("animation_note", ""),
                    "level": p.get("level", ""),
                    "source_start": start,
                    "source_end": end,
                },
            })
    else:
        raise ValueError("Unsupported annotations JSON: expected list, beats, or phrases.")
    return rows[:limit]


def extract_still(video: Path, timestamp: float, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-ss", f"{timestamp:.6f}", "-i", str(video), "-frames:v", "1", "-q:v", "2", str(output)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not output.exists():
        raise RuntimeError(proc.stderr[-2000:])
    return output


def save_project(project_dir: Path, source_video: Path, annotations_path: Path, identity: IdentityLock | None = None, beat_limit: int = 21) -> dict[str, Any]:
    for d in ["source", "identity", "beats", "poses", "generated", "validation", "contact-sheet", "overlays", "exports"]:
        (project_dir / d).mkdir(parents=True, exist_ok=True)
    meta = probe_video(source_video)
    rows = load_beat_annotations(annotations_path, limit=beat_limit)
    detector = MediaPipeLandmarkPipeline()
    beats: list[BeatRecord] = []
    try:
        for row in rows:
            beat_id = int(row.get("beat_id", len(beats)+1))
            ts = float(row["timestamp"])
            source_frame = project_dir / "beats" / f"{beat_id:03d}" / "source.png"
            extract_still(source_video, ts, source_frame)
            lm = detector.extract(source_frame)
            overlay = project_dir / "overlays" / f"beat_{beat_id:03d}.png"
            draw_pose_overlay(source_frame, lm["pose"], overlay, lm.get("status"))
            beat = BeatRecord(
                beat_id=beat_id,
                timestamp=ts,
                source_frame=str(source_frame),
                dance_semantics=row.get("dance_semantics", {}),
                pose=lm["pose"], face=lm["face"], hands=lm["hands"],
                head=lm.get("head", {}), gaze=lm.get("gaze", {}), detector_status=lm.get("status", {}),
            )
            beat_json = project_dir / "beats" / f"{beat_id:03d}" / "beat.json"
            beat_json.parent.mkdir(parents=True, exist_ok=True)
            beat_json.write_text(json.dumps(beat.to_dict(), indent=2) + "\n")
            beats.append(beat)
    finally:
        detector.close()

    manifest = {
        "schema": "stop-motion-lab.project.v1",
        "source_video": str(source_video),
        "annotations": str(annotations_path),
        "video": meta,
        "identity": (identity or IdentityLock()).to_dict(),
        "beat_count": len(beats),
        "beats": [b.to_dict() for b in beats],
    }
    (project_dir / "project.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_project(project_dir: Path) -> dict[str, Any]:
    return json.loads((project_dir / "project.json").read_text())


def generate_beat(project_dir: Path, beat_id: int, adapter: str = "mock") -> dict[str, Any]:
    project = load_project(project_dir)
    beat = next((b for b in project["beats"] if int(b["beat_id"]) == int(beat_id)), None)
    if beat is None:
        raise KeyError(f"Beat {beat_id} not found")
    identity = IdentityLock(**{k:v for k,v in project.get("identity", {}).items() if k in IdentityLock.__dataclass_fields__})
    out = project_dir / "generated" / f"beat_{beat_id:03d}.png"
    result = get_generator(adapter).generate(beat, identity, out)
    if result.path:
        beat["generated_frame"] = result.path
    beat["generation"] = {"ok": result.ok, "adapter": result.adapter, "message": result.message}
    project["beats"] = [beat if int(b["beat_id"]) == int(beat_id) else b for b in project["beats"]]
    (project_dir / "project.json").write_text(json.dumps(project, indent=2) + "\n")
    return beat


def validate_beat(project_dir: Path, beat_id: int) -> dict[str, Any]:
    project = load_project(project_dir)
    beat = next(b for b in project["beats"] if int(b["beat_id"]) == int(beat_id))
    status = beat.get("detector_status", {})
    validation = {
        "pose_similarity": None,
        "identity_consistency": None,
        "face_consistency": None,
        "body_proportion_consistency": None,
        "scene_consistency": None,
        "left_hand": 1.0 if status.get("left_hand") == "PASS" else (0.4 if status.get("left_hand") == "LOW CONFIDENCE" else None),
        "right_hand": 1.0 if status.get("right_hand") == "PASS" else (0.4 if status.get("right_hand") == "LOW CONFIDENCE" else None),
        "feet": beat.get("pose", {}).get("confidence") if beat.get("pose", {}).get("detected") else None,
        "review_required": [],
        "notes": [],
    }
    if not beat.get("generated_frame"):
        validation["review_required"].append("generation missing")
        validation["notes"].append("Identity/pose validation is intentionally not fabricated before a real generation adapter returns an image.")
    if status.get("body_pose") not in ("PASS",):
        validation["review_required"].append("body pose")
    if status.get("face") not in ("PASS",):
        validation["review_required"].append("face")
    beat["validation"] = validation
    (project_dir / "validation" / f"beat_{beat_id:03d}.json").write_text(json.dumps(validation, indent=2) + "\n")
    project["beats"] = [beat if int(b["beat_id"]) == int(beat_id) else b for b in project["beats"]]
    (project_dir / "project.json").write_text(json.dumps(project, indent=2) + "\n")
    return validation


def _fit(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    copy = img.copy().convert("RGB")
    copy.thumbnail(size)
    canvas = Image.new("RGB", size, "black")
    x = (size[0] - copy.width) // 2
    y = (size[1] - copy.height) // 2
    canvas.paste(copy, (x, y))
    return canvas


def build_contact_sheet(project_dir: Path, output: Path | None = None, columns: int = 3) -> Path:
    project = load_project(project_dir)
    beats = project["beats"]
    cell_w, cell_h = 900, 300
    rows = math.ceil(len(beats) / columns)
    sheet = Image.new("RGB", (columns*cell_w, rows*cell_h), (24,24,24))
    draw = ImageDraw.Draw(sheet)
    for i, beat in enumerate(beats):
        r, c = divmod(i, columns)
        x0, y0 = c*cell_w, r*cell_h
        src = _fit(Image.open(beat["source_frame"]), (280, 230))
        overlay_path = project_dir / "overlays" / f"beat_{int(beat['beat_id']):03d}.png"
        overlay = _fit(Image.open(overlay_path), (280,230)) if overlay_path.exists() else src.copy()
        gen = _fit(Image.open(beat["generated_frame"]), (280,230)) if beat.get("generated_frame") and Path(beat["generated_frame"]).exists() else Image.new("RGB", (280,230), (45,45,45))
        sheet.paste(src, (x0+10, y0+52)); sheet.paste(overlay, (x0+305, y0+52)); sheet.paste(gen, (x0+600, y0+52))
        title = f"Beat {int(beat['beat_id']):02d}  {float(beat['timestamp']):.3f}s"
        review = beat.get("validation", {}).get("review_required", [])
        state = "REVIEW" if review else ("GENERATED" if beat.get("generated_frame") else "STRUCTURAL")
        draw.text((x0+12, y0+10), f"{title} — {state}", fill="white")
        sem = beat.get("dance_semantics", {})
        draw.text((x0+12, y0+30), str(sem.get("name") or sem.get("gesture") or "")[:100], fill="white")
        draw.text((x0+10, y0+284), "SOURCE", fill="white")
        draw.text((x0+305, y0+284), "STRUCTURE", fill="white")
        draw.text((x0+600, y0+284), "RECONSTRUCTED", fill="white")
    output = output or project_dir / "contact-sheet" / "contact-sheet.jpg"
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=90)
    return output


def build_timeline_preview(project_dir: Path, output: Path, fps: float = 3.0, prefer_generated: bool = True) -> Path:
    project = load_project(project_dir)
    temp = project_dir / ".timeline"
    shutil.rmtree(temp, ignore_errors=True)
    temp.mkdir(parents=True)
    for i, beat in enumerate(project["beats"], start=1):
        candidate = beat.get("generated_frame") if prefer_generated else None
        src = Path(candidate) if candidate and Path(candidate).exists() else Path(beat["source_frame"])
        shutil.copy2(src, temp / f"f_{i:04d}.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-framerate", str(fps), "-i", str(temp / "f_%04d.png"), "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    shutil.rmtree(temp, ignore_errors=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:])
    return output
