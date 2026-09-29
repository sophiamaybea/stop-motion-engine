# Facial Expression Rules

Facial performance is part of the choreography. It is not decoration added after the body has been posed.

## Core rule

When the source face is readable, **the source performer is authoritative**. Never replace a readable expression with a generic label such as happy, sexy, fierce, sad or focused.

Transfer the changing facial action onto the target identity while preserving the target person's stable facial anatomy.

## Measure per frame

Capture, where visible:
- head yaw, pitch and roll
- gaze direction
- left/right eyelid openness
- blink phase
- brow inner/outer lift
- brow asymmetry
- lower-lid tension
- jaw opening
- jaw lateral displacement
- lip separation
- lip compression
- mouth-corner movement
- cheek tension
- nose/upper-lip movement
- visible effort/breath release

Use MediaPipe blendshapes/landmarks when available, plus source-frame inspection.

## Temporal rules

Expressions must have trajectories, not independent frame prompts.

- A blink must have entry, closure and reopening. Never create a one-frame random blink.
- Gaze often leads or lags the head. Do not weld eyes to skull rotation.
- Jaw/lips may respond to impact and breath a fraction after the body accent.
- Hair/hand occlusion does not reset the face. Preserve the hidden expression state across occlusion.
- On turns, preserve spotting behaviour visible in source.
- On head whips, the facial configuration should transition continuously even when only partly visible.
- Deceleration at the final reach applies to the face too. Do not snap back to neutral on the last frame.

## Anti-style rules

Reject:
- generic glamour face
- permanently parted lips
- permanent pout
- random smile
- exaggerated “fierce” brows
- dead/static eyes while the head moves
- identical expression throughout the dance
- expression changes unsupported by neighbouring frames
- face identity changing because expression becomes extreme

## Target identity

Stable:
- bone structure
- eye shape
- nose structure
- lip anatomy
- jaw/chin
- skin/freckle placement
- hair identity

Variable:
- muscular expression
- gaze
- eyelids
- brows
- mouth/jaw state
- head orientation

The expression-range reference is evidence that the same face can produce large expression changes. It is **not** a menu from which to choose random expressions.

## Phrase emphasis

Important expression-sensitive passages include:
- phrase 3: gaze/head lag through whip
- phrase 6: accent → turn → destabilisation
- phrase 7: release into floor catch, not fear
- phrase 10: collapse/expansion visible in eyes
- phrase 11: softened/half-closed eyes during recline
- phrase 15: continuous expression through hair whip
- phrase 16: small eye/mouth changes are especially important
- phrase 19: micro-responses during rib/shoulder isolations
- phrase 23: face decelerates and settles with final reach

Always consult the source video around the exact timestamp before inventing missing facial information.
