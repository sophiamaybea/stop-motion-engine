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

---

## 7. Body proportions stay constant

The person must not become shorter, wider, more muscular, or differently proportioned between frames.

Maintain leg length, torso length, shoulder width, waist, hip width, arm length, hand size, and head-to-body ratio.

Compare consecutive frames for anthropometric drift. Retarget source geometry onto the **target** skeleton. Never paste source limb lengths onto the locked body.

---

## 8. Clothing is a persistent object

Track garment shape, fabric, seams, straps, waistband, sleeves, footwear, tights, warm-up layers, accessories, hair ties, jewellery.

If a garment moves, it follows physics and body motion. Do not redesign the outfit between frames.

---

## 9. Feet and hands have their own validation

Generative models fail here first. For dance, feet are load-bearing evidence.

Check toe direction, ankle articulation, turnout, arch, pointe / demi-pointe, heel placement, floor contact, and the relationship between leg and foot.

Pointe shoes must behave like pointe shoes. Preserve worn-in visual state when that is the source truth.

---

## 10. Camera is explicit

Track height, distance, focal-length approximation, distortion, horizon, crop, rotation, perspective, and dancer position in frame.

If the reference camera is locked, the virtual camera stays locked. The generator does not wander.

---

## 11. Mirrors obey geometry

A studio mirror is not a second random human.

The reflection has the mirrored pose, correct reflected position, identical clothing and timing, and preserved room geometry and lighting.

Derive the reflection from the primary dancer and camera. Prefer constructing it separately rather than leaving it to the image model. See `references/dance/reference-01/MIRROR_REFLECTION_RULES.md`.

---

## 12. Environment lock

The room does not mutate.

Persist walls, floor, mirror, doors, windows, barre, furniture, lighting, architectural detail.

Generate or reconstruct the background once, then composite the dancer into it. Do not regenerate the entire room every frame.

---

## 13. Frame generation is modular

Each frame is generated from identity reference, body pose, facial expression, outfit state, environment, camera, previous-frame continuity, and next-frame movement target.

Useful tools: ControlNet (pose / depth / edge), IPAdapter, InstantID, ComfyUI workflows, inpainting, pose-guided human generation.

No single model solves everything. Isolate capabilities behind adapters.

---

## 14. Temporal continuity

Frames are generated individually and must still be one sequence.

Compare face, hair, clothing, proportions, background, lighting, camera, hands, feet, shadows, and reflections against neighbours.

The current frame should see previous frame, current target, and next target.

---

## 15. Local repair

Do not regenerate the film because frame 182 has a bad right hand.

Identify the problem, preserve the rest of the frame, inpaint or regenerate the part, compare with 181 and 183, reinsert.

Same path for face, foot, clothing, mirror, background, hair. Project folders already exist: `renders/raw`, `renders/accepted`, `renders/rejected`, `renders/repaired`.

---

## 16. Quality control

Score separately. Do not collapse into one opaque number.

- pose match vs reference
- identity match vs locked face
- temporal consistency vs neighbours
- background consistency
- garment consistency
- face geometry / landmarks
- hand anatomy
- foot pose and contour
- mirror consistency
- scene / camera match

Below-threshold frames enter the repair queue automatically. See `references/dance/reference-01/FRAME_ACCEPTANCE.md`.

---

## 17. Stop-motion render first

Once frames are accepted, assemble them directly.

The first output must remain readable as a frame sequence. Do not hide errors with motion blur or interpolation.

First: clean stop-motion. Then, optionally: smoothed film.

---

## 18. Interpolation is optional and never choreography

Practical-RIFE (or a replacement interpolator) may invent frames **between** approved stills.

If interpolated frames distort hands, face, feet, limbs, mirrors, or clothing, reject them. Choreography comes only from approved keyframes.

---

## 19. This repo is the home

`sophiamaybea/stop-motion-engine` is the orchestration layer.

Do not start a second home for the same system.

Sister repositories supply dance knowledge. Consume them as modules, packages, submodules, or imported datasets. Do not copy their logic into this tree.

- `sophiamaybea/contemporary-studio-dance`
- `sophiamaybea/big-gay-heart-contemporary`
- `sophiamaybea/the-night-they-drove-old-dixie-down-routine`
- `sophiamaybea/dixie-down-contemporary-jazz`

See `docs/ECOSYSTEM.md`.

---

## 20. External systems are interfaces, not a pile

Study useful ideas. Isolate one capability behind one adapter. Respect licences. Never paste proprietary implementations.

FrameFold (`RainerBracharz/framefold`) is a **reference architecture only**: sample → motion/sharpness → rest detection → filter → dedupe → human review → stabilize → assemble. Do not copy its code.

See `docs/ECOSYSTEM.md` and `config/dependencies.toml`.

---

## 21. Dance semantics, not only pixels

Grow a dance-specific record beyond raw coordinates:

```text
movement: travelling arabesque
support_leg: left
working_leg: right
working_leg_height: 72 degrees
torso: forward diagonal
head: left
gaze: upper-left
right_arm: extended
left_arm: trailing
dynamic: suspended
musical_quality: delayed arrival
transition: travelling turn
```

Geometry stays measurable. Language comes from the choreography labs when present.

---

## 22. Musical time

Map frames to beats, subdivisions, accents, phrases, rests, syncopation, sustained notes.

A movement happens in musical time, not only between video timestamps. Record Room / dance-routine-engine own the counted score. This engine stores the mapping, it does not become a second choreographer.

---

## 23. Human review

The user inspects timeline, contact sheet, frame grid, pose overlay, and side-by-side original vs generated.

They click a frame and say: regenerate; fix face / hand / foot; increase turnout; change expression; restore original pose; preserve everything except X.

That triggers a local edit.

---

## 24. End goal

A visual compiler for human movement:

```text
real performance
  -> structured movement data
  -> controlled photographic frames
  -> moving performance
```

Preserve choreography, timing, identity, proportions, facial acting, clothing, camera, environment, mirror geometry, and artistic intent.

**The approved frame sequence is the source of truth.**
