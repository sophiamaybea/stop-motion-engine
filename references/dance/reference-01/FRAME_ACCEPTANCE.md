# Frame Acceptance

Every generated frame must be checked before it enters the accepted sequence.

## Reject immediately for

- wrong source pose or timing
- missing/incorrect hand or foot contact
- wrong floor/airborne state
- target body proportions drifting
- target face/bone structure drifting
- unsupported smile/pout/blink/gaze
- expression discontinuity
- hair length/style changing
- outfit changing
- extra limb/person
- mirror pose mismatch
- mirror identity mismatch
- mirror expression mismatch
- mirror geometry error
- scene/camera/lighting drift

## Separate scores

Record:
- pose_match
- expression_match
- identity_match
- mirror_consistency
- scene_match
- hand_quality
- face_quality
- temporal_consistency

Do not collapse these into one opaque score.

A high identity score must not excuse a wrong dance pose. A beautiful pose must not excuse a wrong facial performance.
