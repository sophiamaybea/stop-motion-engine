# Work Mode Handoff

Build and run against the repository root. Treat this reference directory plus its Drive folder as the first canonical performance specimen.

## First task

1. Load `assets.json`.
2. Fetch the original source video and both pose atlases.
3. Trim/analyse source time 17.0–69.6 seconds.
4. Use the supplied movement blueprint to validate phrase segmentation.
5. Extract DWPose/OpenPose body/hands and MediaPipe facial landmarks/blendshapes.
6. Produce `PERFORMANCE.json`.
7. Compare detected keyframes against the pose atlases.
8. Do **not** render the target identity until extraction/debugging is satisfactory.

## Rendering task

When extraction passes:
- lock target identity
- lock target body proportions
- lock scene/camera
- render each selected performance frame independently but with continuity context
- enforce facial rules
- enforce mirror rules
- reject/repair failed frames
- output stop motion first
- interpolate last

Do not ask a generative video model to perform the choreography from prose.
