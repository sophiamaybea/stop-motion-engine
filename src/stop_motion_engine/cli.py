"""Command line for both directions."""

from __future__ import annotations

import argparse
from pathlib import Path

from .compose import compose_from_frames, write_onion_sheet
from .reverse import reverse_frame_folder, reverse_video


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stop-motion-engine",
        description="Compose stop-motion, or reverse-engineer motion cells from video.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compose", help="stills -> video")
    c.add_argument("frames", type=Path)
    c.add_argument("-o", "--output", type=Path, default=Path("out/stop_motion.mp4"))
    c.add_argument("--fps", type=float, default=12.0)
    c.add_argument("--onion", type=Path, default=None, help="optional onion-skin contact sheet")

    r = sub.add_parser("reverse", help="video -> motion cells")
    r.add_argument("source", type=Path, help="video file or frame folder")
    r.add_argument("-o", "--output", type=Path, default=Path("out/reverse"))
    r.add_argument("--fps", type=float, default=None)
    r.add_argument("--energy", type=float, default=None)
    r.add_argument("--keep-frames", action="store_true")

    d = sub.add_parser("demo", help="synthetic bounce -> compose -> reverse")
    d.add_argument("-o", "--output", type=Path, default=Path("out/demo"))

    args = parser.parse_args(argv)

    if args.cmd == "compose":
        compose_from_frames(args.frames, args.output, fps=args.fps)
        if args.onion:
            write_onion_sheet(args.frames, args.onion)
        print(args.output)
        return 0

    if args.cmd == "reverse":
        src = args.source
        if src.is_dir():
            fps = args.fps if args.fps is not None else 12.0
            score = reverse_frame_folder(src, args.output, fps=fps, energy_override=args.energy)
        else:
            score = reverse_video(
                src, args.output,
                fps_override=args.fps,
                energy_override=args.energy,
                keep_all_frames=args.keep_frames,
            )
        print(f"cells={score.cell_count} frames={score.frame_count} fps={score.fps:.3f}")
        print(args.output / "MOTION_SCORE.json")
        return 0

    if args.cmd == "demo":
        from .demo import run_demo
        print(run_demo(args.output))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
