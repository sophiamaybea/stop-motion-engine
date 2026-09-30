# Onion skin

Onion skin is the inspection layer. It ghosts previous stills through the current one so travel, rotation and limb path are visible without interpolating.

```bash
performance-film onion frames/ -o out/onion.jpg --mode grid --ghosts 2
performance-film onion frames/ -o out/stack.jpg --mode stack
performance-film onion frames/ -o out/seq --mode sequence --ghosts 2
performance-film onion source/ -o out/pair.jpg --mode pair --target renders/raw
```

Modes:

- `grid` — contact sheet, current + N cyan ghosts
- `stack` — every frame ghosted onto the last still
- `sequence` — one repairable PNG per beat
- `pair` — source pose in magenta under the reconstruction. Empty slots stay source-only.

First locked example: https://github.com/sophiamaybea/keiraredpath-petal
