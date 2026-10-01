---
name: blender-video
description: Use when the user wants a video or 3D render made in Blender, especially turning an architecture or data-flow diagram (Mermaid) into an animated 3D scene. Renders headless from scripts so every video is reproducible and reviewable, and covers when to use the interactive Blender MCP instead.
---

# blender-video: diagrams you can fly through

A video that exists only as a live Blender session is a one-off. A video that is
a script plus a render command can be re-rendered when the architecture changes,
reviewed in a PR, and smoke-tested in CI. This skill builds the second kind.

## 3D Mermaid (shipped)

Mermaid flowchart in, MP4 out. Nodes rise rank by rank, edges draw themselves,
then glowing pulses carry data along every edge while the camera orbits.

```bash
python scripts/render.py diagram.mmd -o out.mp4 --direction LR --title "System name"
python scripts/render.py diagram.mmd -o out.mp4 --preview          # half res, 4 samples
python scripts/render.py diagram.mmd -o f.png --still 300          # one frame to check
python scripts/render.py README.md  -o out.mp4                     # first ```mermaid block
```

| Mermaid idea | Becomes in 3D |
|---|---|
| `A[x]` `A(x)` `A([x])` | beveled block; stadium shape reads as "external" |
| `A[(x)]` | cylinder: a datastore |
| `A{x}` | diamond: a decision |
| `A((x))` | sphere |
| `subgraph` | translucent platform lifted into its own tier |
| `-->` `==>` `-.->` | tube, thick tube, thin dim tube (all carry pulses) |
| `\|label\|` | floating label at the arc's peak |
| an edge that closes a cycle | tall loop above the plane, so feedback reads as feedback |
| `classDef fill,stroke,color` | body colour, glowing outline, label colour |

The edge declared *last* in a cycle is treated as the loop back, matching how
people write Mermaid (main flow first, `CUT --> ZOOM` last).

### Rules that keep it readable

- **Match direction to aspect.** `--direction LR` for 16:9, `TD` for 9:16.
  A TD diagram in a landscape frame renders small.
- **Keep labels short.** First line is the title, the rest is the subtitle.
  Past ~25 characters, text is shrunk to fit and stops being readable at 720p.
- **Check stills before a full render.** A full 14s 1080p render takes minutes;
  `--still` at the end frame takes seconds. Look at frame 1 (title), a mid-build
  frame, and the last frame.
- **The camera fits itself.** `fit_camera` searches for the closest distance that
  keeps every node, label and loop in the safe frame through the whole move.
  If something is cropped, it's missing from `frame_points`.

### Files

- `scripts/mermaid3d.py`: parser + layered layout, pure Python, unit tested.
- `scripts/build_scene.py`: runs inside Blender, builds and animates the scene.
- `scripts/render.py`: the one command. Wraps Blender in `xvfb-run` on headless
  Linux (EEVEE needs an OpenGL context; software rendering works, no GPU needed).
- Tested on Blender 4.0 (legacy EEVEE, built-in bloom) and 4.2 (EEVEE Next,
  bloom moved to a compositor glare node). The engine is picked by what the
  installed Blender offers, so either works.
- `--save-blend` writes the `.blend` so you can open it and hand-tune a shot.

## Interactive work: Blender MCP

For exploring looks by conversation, use the community `blender-mcp`
(github.com/ahujasid/blender-mcp): a Blender add-on that opens a local socket,
plus an MCP server Claude connects to. Do not write a new one.

Security: its `execute_blender_code` tool is arbitrary code execution on your
machine. Keep the socket on localhost, enable the add-on only while using it,
and don't open untrusted `.blend` files during a session. When a look is right,
port it into a script here so it becomes reproducible.

## Planned: stop-motion figurines and brick films

Both reuse this pipeline's shape (script in, frames out, ffmpeg):

- **Stop-motion look**: animate on twos (12 fps holds inside 24 fps), constant
  interpolation, a little per-frame jitter on position and light, clay or vinyl
  materials, shallow depth of field, a tabletop set. The look comes from
  *removing* smoothness, so it is cheap to render.
- **Brick films**: build from the LDraw open parts library via an LDraw importer
  add-on instead of modelling bricks. The LEGO name, logo and minifigure design
  are trademarks: fine for personal work, check LEGO's Fair Play policy before
  publishing commercially, and never put the logo in your own branding.
