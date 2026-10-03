from __future__ import annotations

import os
import sys
from pathlib import Path

import gradio as gr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stop_motion_engine.lab import build_contact_sheet, build_timeline_preview, generate_beat, load_project, save_project, validate_beat
from stop_motion_engine.lab_models import IdentityLock
from stop_motion_engine.lab_doctor import system_check


def _path(value):
    if value is None:
        return None
    if isinstance(value, str):
        return Path(value)
    return Path(getattr(value, "name", value))


def analyse(video):
    from stop_motion_engine.lab import probe_video
    if not video:
        return {"error": "Upload a reference video first."}
    return probe_video(_path(video))


def build_project(video, identities, annotations, face_idx, body_idx, profile_idx, hair_idx, outfit_idx, project_name):
    if not video or not annotations:
        return {"error": "Reference video and annotations JSON are required."}, None, None
    refs = [_path(x) for x in (identities or [])]

    def choose(idx):
        try:
            i = int(idx)
            return str(refs[i]) if 0 <= i < len(refs) else None
        except Exception:
            return None

    identity = IdentityLock(
        face_reference=choose(face_idx),
        body_reference=choose(body_idx),
        profile_reference=choose(profile_idx),
        hair_reference=choose(hair_idx),
        outfit_reference=choose(outfit_idx),
    )
    project = ROOT / "projects" / (project_name.strip() or "reference-01")
    manifest = save_project(project, _path(video), _path(annotations), identity=identity, beat_limit=21)
    sheet = build_contact_sheet(project)
    return {"project": str(project), "beat_count": manifest["beat_count"], "video": manifest["video"]}, str(sheet), str(project)


def project_beats(project_path):
    if not project_path:
        return gr.update(choices=[]), []
    p = Path(project_path)
    data = load_project(p)
    choices = [f"{int(b['beat_id']):02d}" for b in data["beats"]]
    gallery = [(b["source_frame"], f"Beat {int(b['beat_id']):02d} · {float(b['timestamp']):.3f}s · {b.get('dance_semantics',{}).get('name','')}") for b in data["beats"]]
    return gr.update(choices=choices, value=choices[0] if choices else None), gallery


def inspect(project_path, beat_choice):
    if not project_path or not beat_choice:
        return None, None, None, {}, {}, {}
    p = Path(project_path)
    data = load_project(p)
    bid = int(beat_choice)
    beat = next(b for b in data["beats"] if int(b["beat_id"]) == bid)
    overlay = p / "overlays" / f"beat_{bid:03d}.png"
    gen = beat.get("generated_frame")
    metrics = beat.get("validation") or {}
    return beat["source_frame"], str(overlay) if overlay.exists() else None, gen, beat.get("dance_semantics", {}), beat.get("detector_status", {}), metrics


def generate(project_path, beat_choice, adapter):
    if not project_path or not beat_choice:
        return None, {"error": "Select a project and beat."}
    beat = generate_beat(Path(project_path), int(beat_choice), adapter)
    validation = validate_beat(Path(project_path), int(beat_choice))
    return beat.get("generated_frame"), {"generation": beat.get("generation"), "validation": validation}


def make_sheet(project_path):
    if not project_path:
        return None
    return str(build_contact_sheet(Path(project_path)))


def preview(project_path, fps):
    if not project_path:
        return None
    p = Path(project_path)
    return str(build_timeline_preview(p, p / "exports" / "preview.mp4", fps=float(fps)))


def check_table():
    rows = []
    for name, item in system_check().items():
        rows.append([name, "✓" if item.get("ok") else "?", str(item.get("detail", ""))])
    return rows


with gr.Blocks(title="Stop Motion Lab") as demo:
    gr.Markdown("# Stop Motion Lab\n**Verification harness:** dance clip → structured performance → identity-locked still frames. Not a generative dance-video tool.")
    project_state = gr.Textbox(label="Current project path", value="", interactive=False)

    with gr.Tab("1 · Project Input"):
        video = gr.Video(label="Reference dance video")
        identities = gr.File(label="Identity references", file_count="multiple", file_types=["image"])
        annotations = gr.File(label="Existing beat annotations JSON", file_types=[".json"])
        gr.Markdown("Identity reference indices are zero-based positions in the uploaded file list.")
        with gr.Row():
            face_idx = gr.Number(label="Face ref index", value=0, precision=0)
            body_idx = gr.Number(label="Full-body ref index", value=1, precision=0)
            profile_idx = gr.Number(label="Profile ref index", value=0, precision=0)
            hair_idx = gr.Number(label="Hair ref index", value=0, precision=0)
            outfit_idx = gr.Number(label="Outfit ref index", value=1, precision=0)
        project_name = gr.Textbox(label="Project name", value="reference-01")
        with gr.Row():
            analyse_btn = gr.Button("Analyse Clip")
            load_btn = gr.Button("Load Existing 21 Beats", variant="primary")
            verify_btn = gr.Button("Run Full Verification")
        metadata = gr.JSON(label="Clip / project metadata")
        initial_sheet = gr.Image(label="21-beat structural contact sheet", type="filepath")
        analyse_btn.click(analyse, inputs=video, outputs=metadata)
        load_btn.click(build_project, inputs=[video,identities,annotations,face_idx,body_idx,profile_idx,hair_idx,outfit_idx,project_name], outputs=[metadata, initial_sheet, project_state])
        verify_btn.click(build_project, inputs=[video,identities,annotations,face_idx,body_idx,profile_idx,hair_idx,outfit_idx,project_name], outputs=[metadata, initial_sheet, project_state])

    with gr.Tab("2 · Source Analysis"):
        refresh = gr.Button("Load project beats")
        beat_gallery = gr.Gallery(label="21 annotated source beats", columns=4, height="auto")
        beat_select = gr.Dropdown(label="Beat", choices=[])
        refresh.click(project_beats, inputs=project_state, outputs=[beat_select, beat_gallery])

    with gr.Tab("3 · Beat Inspector"):
        with gr.Row():
            source_img = gr.Image(label="SOURCE", type="filepath")
            overlay_img = gr.Image(label="STRUCTURE", type="filepath")
            generated_img = gr.Image(label="RECONSTRUCTED", type="filepath")
        semantics = gr.JSON(label="Dance semantics")
        detector_status = gr.JSON(label="Detector status — failures are visible")
        metrics = gr.JSON(label="Separate validation metrics")
        inspect_btn = gr.Button("Inspect selected beat")
        inspect_btn.click(inspect, inputs=[project_state, beat_select], outputs=[source_img,overlay_img,generated_img,semantics,detector_status,metrics])
        adapter = gr.Radio(["mock","comfy","local","remote"], value="mock", label="Generation adapter")
        generate_btn = gr.Button("Generate Selected Beat", variant="primary")
        generation_report = gr.JSON(label="Generation / validation report")
        generate_btn.click(generate, inputs=[project_state,beat_select,adapter], outputs=[generated_img,generation_report])
        with gr.Row():
            gr.Button("Regenerate whole frame")
            gr.Button("Fix face")
            gr.Button("Fix left hand")
            gr.Button("Fix right hand")
            gr.Button("Fix feet")
            gr.Button("Fix pose")
            gr.Button("Fix expression")
            gr.Button("Fix gaze")
            gr.Button("Fix outfit")
        gr.Markdown("Repair controls are intentionally visible in the MVP; specialist repair adapters are not falsely marked implemented.")

    with gr.Tab("Contact Sheet + Timeline"):
        make_sheet_btn = gr.Button("Generate Contact Sheet")
        sheet = gr.Image(label="Source / structure / reconstructed", type="filepath")
        make_sheet_btn.click(make_sheet, inputs=project_state, outputs=sheet)
        fps = gr.Slider(1, 12, value=3, step=1, label="Stop-motion preview FPS")
        preview_btn = gr.Button("Build stop-motion preview")
        preview_video = gr.Video(label="No interpolation")
        preview_btn.click(preview, inputs=[project_state,fps], outputs=preview_video)

    with gr.Tab("System Check"):
        doctor_btn = gr.Button("Refresh system check")
        doctor = gr.Dataframe(headers=["Component","Status","Detail"], datatype=["str","str","str"], interactive=False)
        doctor_btn.click(check_table, outputs=doctor)


if __name__ == "__main__":
    demo.launch(server_name=os.getenv("GRADIO_SERVER_NAME", "0.0.0.0"), server_port=int(os.getenv("PORT", "7860")))
