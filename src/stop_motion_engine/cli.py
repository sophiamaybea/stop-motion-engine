"""Unified command line for stop motion and performance-film workflows."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .compose import compose_from_frames
from .onion import write_onion_sequence, write_onion_sheet, write_pair_onion, write_stack_onion
from .reverse import reverse_frame_folder, reverse_video


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="performance-film",
        description="Reverse-engineer performance, render editable frame sequences, and compose/interpolate film.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compose", help="stills -> stop-motion video")
    c.add_argument("frames", type=Path)
    c.add_argument("-o", "--output", type=Path, default=Path("out/stop_motion.mp4"))
    c.add_argument("--fps", type=float, default=12.0)
    c.add_argument("--onion", type=Path, default=None)

    r = sub.add_parser("reverse", help="video -> picture-change motion cells")
    r.add_argument("source", type=Path)
    r.add_argument("-o", "--output", type=Path, default=Path("out/reverse"))
    r.add_argument("--fps", type=float, default=None)
    r.add_argument("--energy", type=float, default=None)
    r.add_argument("--keep-frames", action="store_true")

    a = sub.add_parser("analyse-performance", help="video -> PERFORMANCE.json + adaptive keyframes")
    a.add_argument("source", type=Path)
    a.add_argument("-o", "--output", type=Path, required=True, help="project directory")
    a.add_argument("--face-model", type=Path, default=None)
    a.add_argument("--pose-json", type=Path, default=None)

    p = sub.add_parser("project-init", help="create an editable performance-film project")
    p.add_argument("directory", type=Path)
    p.add_argument("--source", default=None)

    asm = sub.add_parser("assemble", help="ordered PNGs -> MP4")
    asm.add_argument("frames", type=Path)
    asm.add_argument("-o", "--output", type=Path, required=True)
    asm.add_argument("--fps", type=float, default=12.0)

    smooth = sub.add_parser("smooth", help="Practical-RIFE interpolation")
    smooth.add_argument("source", type=Path)
    smooth.add_argument("-o", "--output", type=Path, required=True)
    smooth.add_argument("--rife-dir", type=Path, default=None)
    smooth.add_argument("--multi", type=int, default=4)
    smooth.add_argument("--fps", type=float, default=None)
    smooth.add_argument("--scale", type=float, default=1.0)

    sub.add_parser("doctor", help="check local engines and optional dependencies")
    sub.add_parser("serve-mcp", help="run the MCP server over stdio")

    onion = sub.add_parser("onion", help="onion-skin a folder of stills — no interpolation")
    onion.add_argument("frames", type=Path)
    onion.add_argument("-o", "--output", type=Path, default=Path("out/onion.jpg"))
    onion.add_argument("--mode", choices=("grid", "stack", "sequence", "pair"), default="grid")
    onion.add_argument("--ghosts", type=int, default=2)
    onion.add_argument("--alpha", type=float, default=0.35)
    onion.add_argument("--columns", type=int, default=7)
    onion.add_argument("--cell-width", type=int, default=240)
    onion.add_argument("--target", type=Path, default=None)
    onion.add_argument("--labels", type=Path, default=None)

    d = sub.add_parser("demo", help="existing synthetic stop-motion round-trip")
    d.add_argument("-o", "--output", type=Path, default=Path("out/demo"))

    args = parser.parse_args(argv)

    if args.cmd == "compose":
        compose_from_frames(args.frames, args.output, fps=args.fps)
        if args.onion:
            write_onion_sheet(args.frames, args.onion)
        print(args.output)
        return 0

    if args.cmd == "onion":
        labels = None
        if args.labels and args.labels.exists():
            labels = [line.strip() for line in args.labels.read_text().splitlines() if line.strip()]
        if args.mode == "grid":
            path = write_onion_sheet(args.frames, args.output, previous_alpha=args.alpha, columns=args.columns, ghosts=args.ghosts, cell_width=args.cell_width, labels=labels)
        elif args.mode == "stack":
            path = write_stack_onion(args.frames, args.output)
        elif args.mode == "sequence":
            written = write_onion_sequence(args.frames, args.output, ghosts=args.ghosts, previous_alpha=args.alpha)
            print(f"wrote {len(written)} onion frames")
            print(args.output)
            return 0
        else:
            if args.target is None:
                parser.error("onion --mode pair requires --target")
            path = write_pair_onion(args.frames, args.target, args.output, columns=args.columns, cell_width=args.cell_width, source_alpha=args.alpha, labels=labels)
        print(path)
        return 0

    if args.cmd == "reverse":
        if args.source.is_dir():
            fps = args.fps if args.fps is not None else 12.0
            score = reverse_frame_folder(args.source, args.output, fps=fps, energy_override=args.energy)
        else:
            score = reverse_video(args.source, args.output, fps_override=args.fps, energy_override=args.energy, keep_all_frames=args.keep_frames)
        print(f"cells={score.cell_count} frames={score.frame_count} fps={score.fps:.3f}")
        print(args.output / "MOTION_SCORE.json")
        return 0

    if args.cmd == "analyse-performance":
        from .analysis import analyse_performance
        result = analyse_performance(args.source, args.output, face_model=args.face_model, pose_json_dir=args.pose_json)
        print(json.dumps({k: str(v) for k, v in result.items()}, indent=2))
        return 0

    if args.cmd == "project-init":
        from .project import init_project
        print(init_project(args.directory, args.source))
        return 0

    if args.cmd == "assemble":
        from .adapters import assemble_frames
        print(assemble_frames(args.frames, args.output, fps=args.fps))
        return 0

    if args.cmd == "smooth":
        from .adapters import run_rife
        rife_dir = args.rife_dir or (Path(os.environ["RIFE_DIR"]) if os.getenv("RIFE_DIR") else None)
        if rife_dir is None:
            parser.error("smooth requires --rife-dir or RIFE_DIR")
        print(run_rife(args.source, args.output, rife_dir, multi=args.multi, fps=args.fps, scale=args.scale))
        return 0

    if args.cmd == "doctor":
        from .doctor import doctor
        print(json.dumps(doctor(), indent=2))
        return 0

    if args.cmd == "serve-mcp":
        from .mcp_server import run
        run()
        return 0

    if args.cmd == "demo":
        from .demo import run_demo
        print(run_demo(args.output))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
