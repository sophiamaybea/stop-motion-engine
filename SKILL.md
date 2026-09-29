---
name: performance-film
aliases: [stop-motion-engine]
description: Local-first performance-to-film engine. Reverse-engineers video into motion cells, adaptive choreography keyframes, body/hand pose and facial performance; retargets proportions; orchestrates frame-by-frame rendering; composes stop motion; optionally interpolates to continuous film.
metadata:
  type: workflow
  version: "0.2.0"
  department: Performance / Film
  github: https://github.com/sophiamaybea/stop-motion-engine
---

# Performance Film

Use this skill when a reference performance must become an editable stop-motion sequence or be transferred to a target identity.

## Governing rule

**Measure first. Retarget second. Generate third. Interpolate last.**

Never ask a generative video model to infer a complex dance when the geometry and timing can be measured from the source video.

## State separation

Keep three independent layers:

- **Identity**: stable facial structure, body proportions, hair, outfit and accessories.
- **Scene**: stable camera, lens, environment and lighting.
- **Performance**: body/hands/head, gaze, facial blendshapes, timing and movement events.

A render should normally alter Performance only.

## Preferred workflow

1. `performance-film project-init PROJECT --source SOURCE`
2. `performance-film analyse-performance SOURCE -o PROJECT ...`
3. Inspect `analysis/PERFORMANCE.json` and `analysis/KEYFRAMES.json`.
4. Retarget geometry to the target skeleton rather than copying the source dancer's proportions.
5. Render local stills via ComfyUI one constrained performance frame at a time.
6. Reject or repair individual frames instead of regenerating the full sequence.
7. `performance-film assemble ...` for true stop motion.
8. Optionally `performance-film smooth ...` with Practical-RIFE.

## Facial performance

Do not replace expression with labels such as happy, sad or sexy. Preserve measured landmarks, head pose, gaze and blendshape coefficients from the source and apply those dynamics to the target identity.

## MCP

Run `performance-film serve-mcp`. Expensive frame/video operations remain local; Work, Grok or another agent should orchestrate tools rather than ingesting every frame.

## Third-party rule

External repositories are engines, not source to paste into this repo. Keep them behind adapters and respect their licences. Never copy proprietary reference implementations into this project.
