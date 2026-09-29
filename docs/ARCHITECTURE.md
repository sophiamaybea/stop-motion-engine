# Performance Film Architecture

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
  -> accepted PNG sequence
  -> stop-motion film
  -> optional interpolation
```

## Why frames first

A video generator is never asked to invent the choreography. The source performance is measured into an editable intermediate representation. The renderer only solves one constrained still at a time. A failed hand, mouth or pose can therefore be regenerated without destroying the rest of the performance.

## Three state layers

- **Identity**: stable face/body/hair/outfit information.
- **Scene**: stable camera/environment/light information.
- **Performance**: pose, hands, head, gaze, facial blendshapes and timing.

Only performance normally changes per frame.

## Third-party boundary

Third-party projects are not copied into this repository. `config/dependencies.toml` records the expected engines. Adapters keep the internal PERFORMANCE schema stable even when a detector, renderer or interpolator is replaced.
