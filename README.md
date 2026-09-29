# Stop Motion Engine

A small bidirectional engine.

**Forward.** Discrete stills become a stop-motion clip.

**Reverse.** A video is treated as if a stop-motion artist shot it. The engine recovers the *cells* — holds punctuated by ticks — and writes `MOTION_SCORE.json`.

The two directions share one unit. A cell is not a frame and not a shot in the film sense. It is the stretch of time where the world did not tick.

```
stills  --compose-->  video
video   --reverse-->  cells + MOTION_SCORE.json
stills  --reverse-->  cells          (same detector, no container)
```

This is the same operation run backwards. Forward you *choose* the ticks. Reverse you *find* them.

## Why this is not pose tracking

Dance / joint analyzers ask *what the body is doing*. This engine asks *when the picture changed enough to count as a new drawing*. That is the stop-motion question. Live-action becomes a stepped score. True stop-motion should nearly round-trip.

## Install

Needs Python 3.10+, numpy, Pillow, and `ffmpeg` / `ffprobe` on PATH.

```bash
pip install -e .
# or
PYTHONPATH=src python -m stop_motion_engine demo -o out/demo
```

## Commands

```bash
# stills → mp4 at 12 fps (classic stop-motion cadence)
python -m stop_motion_engine compose path/to/frames -o out/film.mp4 --fps 12 --onion out/onion.jpg

# video → recovered cells
python -m stop_motion_engine reverse path/to/clip.mp4 -o out/reverse

# synthetic bounce that proves the round trip
python -m stop_motion_engine demo -o out/demo
```

`out/reverse/` contains:

- `MOTION_SCORE.json` — cells, energies, threshold
- `cells/` — one still per recovered hold (the drawing you would have shot)

## MOTION_SCORE schema (v1)

```json
{
  "schema": "stop-motion-engine.motion_score.v1",
  "direction": "reverse",
  "fps": 12.0,
  "frame_count": 24,
  "cell_count": 12,
  "cells": [
    {
      "index": 0,
      "frame_start": 0,
      "frame_end": 1,
      "t0": 0.0,
      "t1": 0.1667,
      "hold_frames": 2,
      "mean_energy": 0.4,
      "peak_energy": 0.6,
      "change_ratio": 0.08,
      "bbox": [48, 80, 96, 128],
      "kind": "hold"
    }
  ]
}
```

Energy is mean absolute luminance difference between adjacent frames. A tick fires when energy clears an adaptive floor (median-cluster of holds vs tail of jumps) and a small fraction of pixels actually moved. The bbox is the changed region on that tick.

## Desk

Engineering desk. Principal: `engineering-technology`. Nearby Stage hand `youtube-joint-frame-analyzer` owns body joints; this engine owns discrete picture-change. Do not merge them.

GitHub: https://github.com/sophiamaybea/stop-motion-engine

## License

MIT.
