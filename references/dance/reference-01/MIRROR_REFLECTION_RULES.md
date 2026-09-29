# Mirror / Reflection Rules — HARD CONSTRAINTS

A mirror reflection is **not another generated dancer**.

It is the same subject, at the same instant, viewed through mirror geometry.

## Non-negotiable

For every frame containing a mirror:

- same identity
- same timestamp
- same body pose
- same joint angles
- same hand/finger state
- same head orientation transformed by reflection geometry
- same facial expression
- same blink phase
- same gaze state transformed geometrically
- same hair state
- same clothing state
- same floor-contact state
- same airborne/contact event

The reflection must not independently improvise.

## Geometry

Treat the mirror as a virtual camera produced by reflecting the real camera through the mirror plane.

Do **not** simply horizontally flip the visible person unless that is geometrically correct for the camera/mirror arrangement.

Preserve:
- mirror plane
- camera position
- subject position
- depth
- perspective
- occlusion
- reflected room/background
- reflected lights/objects
- crop at mirror borders

If part of the real subject is outside the mirror's reflected field of view, it must not magically appear.

## Temporal continuity

A reflection must remain coherent across neighbouring frames.

Reject:
- reflection pose lagging/leading the real subject
- reflection changing expression independently
- hair moving differently without geometric reason
- outfit details switching
- reflection popping in/out
- reflected limb count changing
- a second unrelated woman appearing
- background reflection changing while main room remains fixed

## Rendering strategy

Preferred:
1. render/solve the real subject state
2. project that same solved state through mirror geometry
3. composite both views into the scene
4. run a reflection-consistency check before accepting the frame

Do not run two unrelated generative prompts, one for the person and one for the reflection.

## Acceptance

A mirror frame is rejected if the reflection is aesthetically plausible but physically incompatible with the primary subject.

Physical consistency wins over prettiness.
