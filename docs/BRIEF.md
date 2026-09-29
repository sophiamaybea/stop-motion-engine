# Stop-Motion Dance Engine — Architectural Brief

This is the governing document of `sophiamaybea/stop-motion-engine`.

This system is **not** “make an AI dance video”.

It recreates a real dance performance as a controlled sequence of generated still images, then assembles those stills into motion.

## Why this exists

Do not ask an AI video model to understand or reproduce an entire dance.

Video models are unreliable at preserving exact choreography, body mechanics, timing, facial expression, identity, clothing, hands, feet, reflections and camera geometry across a long sequence.

Instead, break the performance into a sequence of individually controlled visual states.

```text
reference dance video
  -> analyse movement and face
  -> extract important moments
  -> describe each moment precisely
  -> generate each frame under constraints
  -> verify continuity
  -> assemble stop motion
  -> optionally interpolate
```

**The approved image frames are the source of truth.**
The final video is a rendering of those frames.

Governing principles:

1. Never ask a generative model to remember something the system can explicitly constrain.
2. Measure first. Retarget second. Generate third. Interpolate last.
3. Repair locally. Do not regenerate the whole film because one hand is wrong.

---

## 1. Input

The user provides a dance reference video. It may contain full-body choreography, travel, turns, jumps, floorwork, arm gestures, head movement, facial expressions, clothing interaction, eyeline changes, mirror reflections, and camera perspective changes.

Analyse the original dance. Do not invent a new interpretation of it. The goal is the actual choreography and performance quality.

Dance-specific assets for the first locked reference live in `references/dance/reference-01/`. Heavy media stays on Drive; this repo keeps the rules and indexes.

---

## 2. Analyse the original video

Extract both **geometry** and **performance information**.

Geometry includes body pose, joint positions, torso and pelvis orientation, support vs free leg, turnout, foot articulation, heel height, relevé or pointe where relevant, knee direction, arm and hand position, head angle, eye direction, spine shape, shoulder placement, centre of gravity, travel direction, rotation, acceleration, deceleration, suspension, balance, and transitions.

A skeleton is not enough. It does not say how the movement feels, where the weight is, what the dancer is anticipating, whether the phrase is sharp or released, whether the torso leads, whether the head arrives before or after the body, whether the dancer is resisting momentum, or how a gesture is phrased.

Every analysed moment must carry both layers.

Sister choreography labs (`contemporary-studio-dance` and the routine repos) own movement vocabulary. This engine consumes their outputs. It does not rebuild them.

---

## 3. Facial performance is choreography

The face is not optional cosmetics.

Capture expression, eyebrow position, eye openness, gaze, mouth shape, smile intensity, tension, cheek movement, head inclination, looks-to-camera vs looks-away, effort-caused change, and musical-interpretation change.

Synchronise facial performance with the corresponding body frame. Do not stamp a neutral face onto every still.

Do not replace measured dynamics with labels such as happy, sad, or sexy.

---

## 4. Keyframes are adaptive

Do not sample at a fixed interval.

Select frames from movement information:

- start and end of a phrase
- maximum extension and deepest contraction
- direction change
- take-off, peak of jump, landing
- foot contact and weight transfer
- turn initiation and completion
- head accent, arm accent, expression change
- unusual silhouette
- fast transitional movement that needs extra frames

Sparse where the dance holds. Dense where it is technically complex.

Implementation today: motion energy + optional pose delta + optional expression delta → `KEYFRAMES.json`. Picture-change cells remain in `MOTION_SCORE.json`. Both are signals. Neither is the whole dance.

---

## 5. Every frame is a structured record

A frame must never exist merely as an image. It also exists as a description of what that image is supposed to contain, so it can be regenerated, compared, and repaired.

Canonical performance track: `analysis/PERFORMANCE.json` (`stop-motion-engine.performance.v1`).

Target per-frame record (grow toward this; do not invent conflicting schemas):

```json
{
  "frame": 127,
  "timestamp": 8.42,
  "body_pose": {},
  "left_foot": {},
  "right_foot": {},
  "hands": {},
  "head": {},
  "face": {},
  "gaze": {},
  "camera": {},
  "reflection": {},
  "movement_quality": {},
  "continuity_constraints": {},
  "generation_prompt": ""
}
```

---

## 6. Identity is a hard constraint

The dancer must remain recognisably the same person.

Use reference images and identity-conditioning (InstantID, IPAdapter, embeddings, LoRA) where useful.

Identity must not override pose accuracy. Both stay.

Do not allow gradual change of facial structure, nose, eye shape, eye colour, body proportions, limb length, torso proportions, hair, or skin tone.

Looks-like-me / locked identity stills are the identity source. This engine does not invent a new face.
