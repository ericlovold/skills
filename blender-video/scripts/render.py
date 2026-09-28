"""One command: Mermaid in, MP4 out.

  python render.py ../README.md -o skills.mp4 --direction LR --title "ericlovold/skills"
  python render.py arch.mmd -o arch.mp4 --res 1280x720 --preview      # fast draft
  python render.py arch.mmd -o frame.png --still 300                  # one frame to check

Steps: mermaid3d.py (parse + layout) -> Blender headless (build + render PNG frames) -> ffmpeg (H.264).
Frames are kept next to the output so a crashed render can be inspected; delete them when done.
On Linux without a display, EEVEE needs a virtual one, so Blender is wrapped in xvfb-run when present.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mermaid3d  # noqa: E402


def blender_cmd() -> list[str]:
    exe = os.environ.get("BLENDER") or shutil.which("blender")
    mac = "/Applications/Blender.app/Contents/MacOS/Blender"
    if not exe and os.path.exists(mac):
        exe = mac
    if not exe:
        sys.exit("Blender not found. Install it or set BLENDER=/path/to/blender")
    cmd = [exe, "-b", "--factory-startup"]
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
        cmd = ["xvfb-run", "-a", "-s", "-screen 0 1280x720x24"] + cmd
    return cmd


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help=".mmd file or Markdown with a ```mermaid block")
    ap.add_argument("-o", "--out", required=True, help=".mp4 (animation) or .png (with --still)")
    ap.add_argument("--direction", choices=["TD", "BT", "LR", "RL"])
    ap.add_argument("--title", default="")
    ap.add_argument("--seconds", type=float, default=14.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--res", default="1920x1080", help="e.g. 1920x1080, 1080x1920 for vertical")
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--still", type=int, help="render just this frame")
    ap.add_argument("--preview", action="store_true", help="half resolution, 4 samples, for fast iteration")
    ap.add_argument("--save-blend", help="also write the .blend to open and tweak by hand")
    args = ap.parse_args(argv)

    with open(args.source, encoding="utf-8") as fh:
        g = mermaid3d.parse(fh.read())
    if args.direction:
        g.direction = args.direction
    g = mermaid3d.layout(g)

    res, samples = args.res, args.samples
    if args.preview:
        w, h = (int(v) for v in res.lower().split("x"))
        res, samples = f"{w // 2}x{h // 2}", 4

    out = os.path.abspath(args.out)
    work = tempfile.mkdtemp(prefix="bv_")
    graph_json = os.path.join(work, "graph.json")
    with open(graph_json, "w", encoding="utf-8") as fh:
        json.dump(g.to_json(), fh)

    frames_dir = os.path.splitext(out)[0] + "_frames"
    target = out if args.still is not None else frames_dir
    cmd = blender_cmd() + ["--python", os.path.join(HERE, "build_scene.py"), "--",
                           "--graph", graph_json, "--out", target, "--seconds", str(args.seconds),
                           "--fps", str(args.fps), "--res", res, "--samples", str(samples),
                           "--title", args.title]
    if args.still is not None:
        cmd += ["--still", str(args.still)]
    if args.save_blend:
        cmd += ["--save-blend", os.path.abspath(args.save_blend)]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    if args.still is not None:
        print(f"wrote {out}")
        return 0

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print(f"ffmpeg not found; frames are in {frames_dir}")
        return 1
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-framerate", str(args.fps),
                    "-i", os.path.join(frames_dir, "f_%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow",
                    "-movflags", "+faststart", out], check=True)
    print(f"wrote {out} (frames kept in {frames_dir})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
