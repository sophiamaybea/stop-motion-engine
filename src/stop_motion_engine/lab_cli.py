from __future__ import annotations

import argparse
import json
from pathlib import Path

from .lab import build_contact_sheet, build_timeline_preview, generate_beat, load_project, probe_video, save_project, validate_beat
from .lab_models import IdentityLock
from .lab_doctor import system_check


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="stopmotion")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyse")
    a.add_argument("video", type=Path)

    b = sub.add_parser("beats")
    b.add_argument("project", type=Path)
    b.add_argument("--video", type=Path)
    b.add_argument("--annotations", type=Path)
    b.add_argument("--face", type=Path)
    b.add_argument("--body", type=Path)

    g = sub.add_parser("generate")
    g.add_argument("project", type=Path)
    g.add_argument("--beat", type=int, required=True)
    g.add_argument("--adapter", choices=["mock","local","comfy","remote"], default="mock")

    v = sub.add_parser("validate")
    v.add_argument("project", type=Path)
    v.add_argument("--beat", type=int, default=1)

    c = sub.add_parser("contact-sheet")
    c.add_argument("project", type=Path)

    t = sub.add_parser("preview")
    t.add_argument("project", type=Path)
    t.add_argument("--fps", type=float, default=3.0)

    sub.add_parser("doctor")

    args = p.parse_args(argv)
    if args.cmd == "analyse":
        print(json.dumps(probe_video(args.video), indent=2)); return 0
    if args.cmd == "beats":
        if not args.video or not args.annotations:
            if (args.project / "project.json").exists():
                print(json.dumps(load_project(args.project), indent=2)); return 0
            p.error("beats requires --video and --annotations when the project does not exist")
        identity = IdentityLock(face_reference=str(args.face) if args.face else None, body_reference=str(args.body) if args.body else None)
        out = save_project(args.project, args.video, args.annotations, identity=identity)
        print(json.dumps({"project": str(args.project), "beat_count": out["beat_count"], "video": out["video"]}, indent=2)); return 0
    if args.cmd == "generate":
        print(json.dumps(generate_beat(args.project, args.beat, args.adapter), indent=2)); return 0
    if args.cmd == "validate":
        print(json.dumps(validate_beat(args.project, args.beat), indent=2)); return 0
    if args.cmd == "contact-sheet":
        print(build_contact_sheet(args.project)); return 0
    if args.cmd == "preview":
        print(build_timeline_preview(args.project, args.project / "exports" / "preview.mp4", fps=args.fps)); return 0
    if args.cmd == "doctor":
        print(json.dumps(system_check(), indent=2)); return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
