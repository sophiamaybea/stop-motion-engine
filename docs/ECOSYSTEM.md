# Ecosystem

This repo is the single home for the stop-motion / performance-film system. Everything else is either a **sister module** (ours) or an **external adapter** (theirs).

Do not glue twenty apps together. Name the capability, then point at one interface.

## Pipeline the ecosystem serves

```text
dance / reference video
  -> movement + face analysis
  -> pose / keyframe selection
  -> stop-motion-engine
  -> generate the locked identity at those exact poses
  -> enforce face / expression / outfit / hand / feet / mirror rules
  -> assemble frames
  -> optional RIFE interpolation
  -> final dance film
```

## Sister modules (ours)

Consume. Do not fork their useful logic into this tree.

| Repo | Role |
| --- | --- |
| [sophiamaybea/stop-motion-engine](https://github.com/sophiamaybea/stop-motion-engine) | Orchestration. Cells, scores, project layout, adapters, assemble, interpolate. |
| [sophiamaybea/contemporary-studio-dance](https://github.com/sophiamaybea/contemporary-studio-dance) | Movement vocabulary, kinematics, style critic, CustomDance intent. |
| [sophiamaybea/big-gay-heart-contemporary](https://github.com/sophiamaybea/big-gay-heart-contemporary) | Routine-specific counted score and performance lock. |
| [sophiamaybea/the-night-they-drove-old-dixie-down-routine](https://github.com/sophiamaybea/the-night-they-drove-old-dixie-down-routine) | Routine-specific counted score. |
| [sophiamaybea/dixie-down-contemporary-jazz](https://github.com/sophiamaybea/dixie-down-contemporary-jazz) | Routine-specific counted score. |

First locked dance asset pack: `references/dance/reference-01/` in this repo. Media on Drive, rules in git.

## Capability map

Keep these folders conceptual even before every adapter exists:

```text
pose_extractor/
identity_engine/
expression_engine/
scene_engine/
frame_generator/
reflection_engine/
quality_control/
frame_repair/
interpolation/
renderer/
choreography_module/   # sister dance repos
```

## External systems — what we take

Architecture or one capability only. Licence-check before any local checkout. Never vendor proprietary source.

### Study architecture, do not copy code

| Project | Take |
| --- | --- |
| [RainerBracharz/framefold](https://github.com/RainerBracharz/framefold) | Video → sample → motion/sharpness → rest/hold detection → filter junk frames → dedupe → human review → stabilize → assemble. Commercial / not a licence to reuse source. |
| [brick-a-brack/eagle-animation](https://github.com/brick-a-brack/eagle-animation) | Capture timeline, onion skin, frame organisation, preview. |
| [charlielee/boats-animator](https://github.com/charlielee/boats-animator) | Desktop capture, onion skin, instant playback, export. |
| [tahoma2d/tahoma2d](https://github.com/tahoma2d/tahoma2d) | Large 2D / stop-motion package. Study timeline and xsheet ideas. |
| [kundanbhosale/dual-camera-stop-motion-studio](https://github.com/kundanbhosale/dual-camera-stop-motion-studio) | Dual-camera reference + capture. |
| [tmoody1973/pasteup](https://github.com/tmoody1973/pasteup) | Frame assembly / animation tooling ideas. |
| [tmoody1973/paper-film](https://github.com/tmoody1973/paper-film) | Frame-based film construction ideas. |
| [AdvancedHobbyLab/FramePhantom](https://github.com/AdvancedHobbyLab/FramePhantom) | Stop-motion / frame workflow ideas. |
| [bomkino/tiny-voices](https://github.com/bomkino/tiny-voices) | Frame-generation reference only. |
| [cgallic/cartoonimator](https://github.com/cgallic/cartoonimator) | Held-shot compositor: timed stills → MP4. Useful assemble metaphor. |

### Intended local adapters (not vendored)

| Project | Capability |
| --- | --- |
| [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | Local still renderer. |
| [Comfy-Org/comfy-mcp](https://github.com/Comfy-Org/comfy-mcp) | Optional external Comfy MCP. This repo also exposes its own MCP. |
| [Fannovel16/comfyui_controlnet_aux](https://github.com/Fannovel16/comfyui_controlnet_aux) | DWPose / OpenPose / depth / edge preprocessors. |
| [cubiq/ComfyUI_IPAdapter_plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus) | Appearance consistency between frames. |
| [instantX-research/InstantID](https://github.com/instantX-research/InstantID) | Identity lock. |
| [hzwer/Practical-RIFE](https://github.com/hzwer/Practical-RIFE) | Interpolation after approved stills. MIT. |
| [IDEA-Research/DWPose](https://github.com/IDEA-Research/DWPose) | Whole-body pose. Apache-2.0. |
| [google-ai-edge/mediapipe](https://github.com/google-ai-edge/mediapipe) | Face landmarks, blendshapes, head transform. Apache-2.0. |

### Motion-generation research — optional later modules

These are **not** the source of choreography. They may later help retarget or repair local motion. The approved stills still win.

| Project | Possible later use |
| --- | --- |
| [TMElyralab/MusePose](https://github.com/TMElyralab/MusePose) | Pose alignment between dance video and reference person. |
| [Tencent/MimicMotion](https://github.com/Tencent/MimicMotion) | Reference-person + motion-guided animation. |
| [Wan-Video/Wan-Dancer](https://github.com/Wan-Video/Wan-Dancer) | Dance-specific generation research. Hierarchical keyframe ideas only. |
| [Wan-Video/Wan-Animate](https://github.com/Wan-Video/Wan-Animate) | Character animation / motion transfer research. |
| [XulongT/CustomDance](https://github.com/XulongT/CustomDance) | Controllable 3D dance, local motion repair, joint-group edit, SMPL export. Already approached via `contemporary-studio-dance`. |
| [trajeshbe/dance](https://github.com/trajeshbe/dance) | Movement modelling reference. |
| [godzillalla/Dance-Synthesis-Project](https://github.com/godzillalla/Dance-Synthesis-Project) | Synthesis reference. |
| [AMAP-ML/MACE-Dance](https://github.com/AMAP-ML/MACE-Dance) | Motion research. |
| [oceanflowlab/AtomicDance](https://github.com/oceanflowlab/AtomicDance) | Motion research. |

If a research video model is used at all, it renders **one constrained frame or a short repair**, never the whole dance from a prompt.
