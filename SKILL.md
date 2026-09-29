---
name: stop-motion-engine
description: Bidirectional stop-motion engine. Compose discrete stills into a clip, or reverse-engineer any video into motion cells (holds and ticks) and MOTION_SCORE.json. Triggers include stop motion, stop-motion, create stop motion, understand stop motion, reverse engineer motion, motion cells from video, onion skin, MOTION_SCORE.
metadata:
  type: workflow
  version: "0.1.0"
  department: Engineering
  desk_role: hand
  principal: engineering-technology
  os: universal-living-genius-os
  github: https://github.com/sophiamaybea/stop-motion-engine
---

## OS gate

Desk: Engineering. Role: hand. Principal: `engineering-technology`. Frame through Universal Living Genius OS. Body joints stay with `youtube-joint-frame-analyzer`. Pictures of the user stay with `looks-like-me`. Music stays in the Record Room. Do not spawn a sibling skill from inside this file.

# Stop Motion Engine

One unit both ways. A **cell** is a hold punctuated by a tick. Forward you choose the ticks. Reverse you find them.

## When to activate

- Create a stop-motion clip from a folder of stills
- Recover the discrete drawings that would have made a video
- Understand motion in a video as stepped picture-change, not as pose
- Produce `MOTION_SCORE.json` for another agent
- Onion-skin a sequence

Do not activate for Mixamo/SMPL joint timelines. That is Stage.

## Commands

```bash
PYTHONPATH=src python -m stop_motion_engine compose FRAMES_DIR -o out/film.mp4 --fps 12 --onion out/onion.jpg
PYTHONPATH=src python -m stop_motion_engine reverse VIDEO.mp4 -o out/reverse
PYTHONPATH=src python -m stop_motion_engine demo -o out/demo
```
