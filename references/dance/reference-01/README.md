# Dance Reference 01 — full performance asset pack

This directory is the canonical handoff for the first full dance used by the Performance Film engine.

## Actual media

The heavy media is stored in the connected Google Drive folder rather than duplicated in Git history:

**Drive folder:** https://drive.google.com/drive/folders/1z63RLEHQZfI23qG_FGG3Ez39DB-M3snd

The folder contains the actual:
- original screen recording
- 6 fps stop-motion performance reference
- pose atlas covering phrases 1–12 (start/mid/end)
- pose atlas covering phrases 13–23 (start/mid/end)
- key-pose contact sheet
- full-body/mirror identity reference
- master face reference
- expression-range grid
- DANCELAB skeleton-overlay reference
- movement blueprint JSON and CSV

The source dance occupies **00:17.0–01:09.6** of the original screen recording (52.6 seconds).

## Authority order

When evidence conflicts:

1. source-video timing and geometry
2. readable source facial performance
3. target identity anatomy/body proportions
4. phrase-level expression guidance
5. aesthetic improvisation

Never alter choreography, expression, contact geometry or mirror behaviour merely because a different render looks prettier.

## Workflow

1. Read `assets.json`.
2. Inspect the source and both pose atlases before rendering.
3. Use the movement blueprint as the phrase/timing map.
4. Extract body/hands/head/face from source.
5. Retarget movement to target proportions.
6. Render target stills one performance frame at a time.
7. Apply `FACIAL_EXPRESSION_RULES.md`.
8. Apply `MIRROR_REFLECTION_RULES.md`.
9. Reject bad frames using `FRAME_ACCEPTANCE.md`.
10. Assemble stop motion.
11. Interpolate only after choreography and expressions are correct.

The pose atlases are not decorative moodboards. They are **source-performance assets** and must be treated as measurable choreography evidence.
