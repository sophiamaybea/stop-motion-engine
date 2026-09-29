# Stop Motion Engine / Performance Film

A local-first engine for going both directions:

```text
stills -> stop motion
video  -> motion cells
video  -> structured body + facial performance -> target frames -> film
```

The rule is **measure first, generate second**. A video model is never asked to guess an entire dance. The source performance is converted into an editable intermediate representation; the target person can then be rendered one constrained frame at a time; interpolation happens last.

## v0.2

This branch adds:

- the existing bidirectional stop-motion compose/reverse engine
- `MOTION_SCORE.json` picture-change analysis
- canonical `PERFORMANCE.json`
- adaptive keyframe selection using motion, pose change and facial-expression change
- MediaPipe Face Landmarker support for landmarks, blendshapes, transform matrix and head pose
- DWPose/OpenPose-compatible JSON input for body/hands
- deterministic proportion-aware 2D skeletal retargeting
- canonical editable project layout
- local ComfyUI queue adapter
- Practical-RIFE interpolation wrapper
- FFmpeg frame assembly
- a single MCP server for agent orchestration

Third-party engines are **not vendored** into the repo. They sit behind adapters, so the renderer or detector can be replaced without changing the performance representation.

## Install

Core:

```bash
pip install -e .
```

Performance extraction + MCP:

```bash
pip install -e '.[performance,mcp]'
```

Or run:

```bash
./install.sh
performance-film doctor
```

FFmpeg/ffprobe must be on PATH.

## Analyse a performance

```bash
performance-film project-init projects/dance-01 --source source.mp4

performance-film analyse-performance source.mp4 \
  -o projects/dance-01 \
  --face-model models/face_landmarker.task \
  --pose-json poses/source
```

The pose directory is OpenPose-compatible JSON, so DWPose/OpenPose/ComfyUI preprocessors can feed the same boundary.

Outputs include:

```text
analysis/MOTION_SCORE.json
analysis/KEYFRAMES.json
analysis/PERFORMANCE.json
analysis/cells/
source/frames/
```

## Stop motion

```bash
performance-film assemble projects/dance-01/renders/accepted \
  -o projects/dance-01/exports/stopmotion.mp4 --fps 12
```

Existing commands remain:

```bash
performance-film compose frames/ -o out/stop.mp4 --fps 12
performance-film reverse clip.mp4 -o out/reverse --keep-frames
```

## Smooth to continuous film

Practical-RIFE is external:

```bash
export RIFE_DIR=/path/to/Practical-RIFE
performance-film smooth projects/dance-01/exports/stopmotion.mp4 \
  -o projects/dance-01/exports/film.mp4 --multi 2
```

It can also receive a numerically named PNG directory.

## MCP

```bash
performance-film serve-mcp
```

Current MCP tools:

- `environment_status`
- `create_project`
- `analyse_video`
- `assemble_stopmotion`
- `queue_comfy_workflow`

The calling agent orchestrates the pipeline; expensive pose, face, rendering and interpolation work stays local.

## Architecture

See `docs/ARCHITECTURE.md`.

The engine separates:

1. **Identity** — face, body proportions, hair, outfit.
2. **Scene** — camera, environment, lens, lighting.
3. **Performance** — pose, hands, head, gaze, expression and timing.

Only Performance should normally change from frame to frame.

## Intended local stack

- DWPose / OpenPose-compatible preprocessing
- Google MediaPipe Face Landmarker
- ComfyUI
- Practical-RIFE
- FFmpeg

No paid image/video API is required by the architecture.

## Licence

MIT for this repository. External engines and models retain their own licences.
