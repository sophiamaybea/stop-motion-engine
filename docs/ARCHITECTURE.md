# Performance Film Architecture

Read `docs/BRIEF.md` first. That document is why the system exists. This file is how the current code is shaped.

The engine separates **measurement** from **generation**.

```text
source performance
  -> decode/cache frames
  -> picture-change / motion signal
  -> DWPose/OpenPose-compatible pose signal
  -> MediaPipe facial blendshape + head signal
  -> adaptive performance keyframes
  -> proportion-aware target skeleton
  -> local still-image renderer (ComfyUI)
  -> per-frame quality control + local repair
  -> accepted PNG sequence
  -> stop-motion film
  -> optional interpolation
```

## Why frames first

A video generator is never asked to invent the choreography. The source performance is measured into an editable intermediate representation. The renderer only solves one constrained still at a time. A failed hand, mouth or pose can therefore be regenerated without destroying the rest of the performance.

## Three state layers

- **Identity**: stable face/body/hair/outfit information.
- **Scene**: stable camera/environment/light information.
- **Performance**: pose, hands, head, gaze, facial blendshapes, timing, and movement quality.

Only performance normally changes per frame.

## Contracts

- `MOTION_SCORE.json` — picture-change cells (`stop-motion-engine.motion_score.v1`)
- `KEYFRAMES.json` — adaptive important frames (`stop-motion-engine.keyframes.v1`)
- `PERFORMANCE.json` — structured performance track (`stop-motion-engine.performance.v1`)
- `manifest.json` — project reproducibility (`stop-motion-engine.project.v1`)

A cell is a hold punctuated by a tick. A keyframe is an important performance state. A performance frame is the record that generation and repair must satisfy. Do not collapse these three into one list.

## Module boundary

Conceptual engines (see `docs/ECOSYSTEM.md`):

```text
pose_extractor
identity_engine
expression_engine
scene_engine
frame_generator
reflection_engine
quality_control
frame_repair
interpolation
renderer
choreography_module
```

Today the Python package implements compose, reverse, analyse-performance, project layout, 2D retarget, ComfyUI queue, RIFE wrapper, assemble, doctor, and MCP. Missing modules stay as interfaces plus rules under `references/dance/`, not as pasted third-party trees.

## FrameFold lesson (architecture only)

Useful shape, not source: sample the video, score motion and sharpness, detect holds, drop junk frames, deduplicate, let a human review, stabilize, then assemble. We already own hold/tick detection via luminance energy. We do not copy FrameFold code or models.

## Third-party boundary

Third-party projects are not copied into this repository. `config/dependencies.toml` records the expected engines. Adapters keep the internal PERFORMANCE schema stable even when a detector, renderer or interpolator is replaced.
