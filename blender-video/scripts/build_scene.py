"""Build and render a 3D data-flow diagram in Blender from mermaid3d.py's layout JSON.

Runs inside Blender:
  blender -b --factory-startup --python build_scene.py -- --graph graph.json --out frames/

Scene grammar (what each Mermaid idea becomes):
  node        beveled block (shape from Mermaid), fill = classDef fill, glowing outline = stroke
  subgraph    translucent platform the member nodes stand on, lifted into its own tier
  edge        tube arcing through 3D space; longer edges arc higher so crossings separate
  back edge   a tall loop, so feedback reads as feedback
  data flow   glowing pulses travelling along each edge, source to sink
  timeline    nodes rise rank by rank, edges draw themselves, then data flows while the camera orbits
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

DEFAULT_CLASS = {"fill": "#1c2330", "stroke": "#5b8def", "color": "#e8eef7"}
BG = "#070b10"
FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/System/Library/Fonts/Supplemental", "C:/Windows/Fonts"]
FONT_REGULAR = ["DejaVuSans.ttf", "Arial.ttf", "arial.ttf"]
FONT_BOLD = ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"]

NODE_W, NODE_D, NODE_H = 3.0, 1.3, 0.6


# ---------------------------------------------------------------- helpers


def args_after_dashdash() -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="build_scene.py")
    ap.add_argument("--graph", required=True)
    ap.add_argument("--out", required=True, help="directory for PNG frames, or a .png path with --still")
    ap.add_argument("--seconds", type=float, default=14.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--title", default="")
    ap.add_argument("--still", type=int, default=None, help="render only this frame to --out")
    ap.add_argument("--save-blend", default=None, help="also save the .blend for hand-tuning")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return ap.parse_args(argv)


def hex_to_linear(h: str, alpha: float = 1.0) -> tuple:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, alpha)


def find_font(names: list[str]):
    for d in FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return bpy.data.fonts.load(p, check_existing=True)
    return None


_mat_cache: dict[tuple, bpy.types.Material] = {}


def mat_surface(name: str, color: str, rough: float = 0.45, emit: str | None = None,
                emit_strength: float = 0.0, alpha: float = 1.0, metallic: float = 0.0):
    key = ("surf", color, rough, emit, emit_strength, alpha, metallic)
    if key in _mat_cache:
        return _mat_cache[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = hex_to_linear(color)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metallic
    if emit:
        p.inputs["Emission Color"].default_value = hex_to_linear(emit)
        p.inputs["Emission Strength"].default_value = emit_strength
    if alpha < 1.0:
        p.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
        m.shadow_method = "NONE"
        m.show_transparent_back = False
    _mat_cache[key] = m
    return m


def mat_emit(name: str, color: str, strength: float, cull_back: bool = False):
    key = ("emit", color, strength, cull_back)
    if key in _mat_cache:
        return _mat_cache[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = hex_to_linear(color)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    m.use_backface_culling = cull_back
    _mat_cache[key] = m
    return m


def link(obj, collection):
    collection.objects.link(obj)
    return obj


def key_scale(obj, frame: int, s: float, interp: str = "BEZIER"):
    obj.scale = (s, s, s)
    obj.keyframe_insert("scale", frame=frame)
    for fc in obj.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            if kp.co.x == frame:
                kp.interpolation = interp


def pop_in(obj, start: int, final: float = 1.0):
    """Scale 0 -> overshoot -> settle. Reads as the object arriving, not fading."""
    key_scale(obj, start - 1, 0.0, "CONSTANT")
    key_scale(obj, start, 0.001)
    key_scale(obj, start + 9, final * 1.08)
    key_scale(obj, start + 15, final)


def billboard(obj, camera):
    c = obj.constraints.new("TRACK_TO")
    c.target = camera
    c.track_axis = "TRACK_Z"
    c.up_axis = "UP_Y"


def make_text(body: str, font, size: float, color: str, strength: float, coll, max_width: float | None = None):
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    if font:
        cu.font = font
    ob = link(bpy.data.objects.new("txt", cu), coll)
    ob.data.materials.append(mat_emit("text", color, strength))
    if max_width:
        bpy.context.view_layer.update()
        if ob.dimensions.x > max_width:
            cu.size = size * max_width / ob.dimensions.x
    return ob


def bezier(points: list[Vector], name: str, coll, depth: float):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 24
    cu.bevel_depth = depth
    cu.bevel_resolution = 4
    cu.use_fill_caps = True
    cu.bevel_factor_mapping_end = "SPLINE"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    return link(bpy.data.objects.new(name, cu), coll)


# ---------------------------------------------------------------- scene pieces


def node_mesh(shape: str, coll):
    if shape == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.95, depth=1.0)
        h = 1.0
    elif shape == "circle":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.85)
        h = 1.7
    elif shape == "diamond":
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        ob = bpy.context.active_object
        ob.scale = (1.9, 1.9, NODE_H)
        ob.rotation_euler.z = math.radians(45)
        h = NODE_H
    else:
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        bpy.context.active_object.scale = (NODE_W, NODE_D, NODE_H)
        h = NODE_H
    ob = bpy.context.active_object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    for c in ob.users_collection:
        c.objects.unlink(ob)
    coll.objects.link(ob)
    if shape not in ("circle", "cylinder"):
        bev = ob.modifiers.new("bevel", "BEVEL")
        bev.width = {"stadium": 0.29, "round": 0.2}.get(shape, 0.1)
        bev.segments = 6
        bev.limit_method = "ANGLE"
    else:
        bpy.ops.object.shade_smooth()
    # Inverted-hull outline: a flipped, back-face-culled shell drawn in the stroke colour.
    sol = ob.modifiers.new("outline", "SOLIDIFY")
    sol.thickness = 0.05
    sol.offset = 1.0
    sol.use_flip_normals = True
    sol.use_rim = False
    sol.material_offset = 1
    return ob, h


def set_camera_path(cam, dist: float, frames: int):
    """Start high and wide, end slightly lower and closer: a slow push-in."""
    if cam.animation_data:
        cam.animation_data_clear()
    cam.location = (0, -dist, dist * 0.8)
    cam.keyframe_insert("location", frame=1)
    cam.location = (0, -dist * 0.9, dist * 0.68)
    cam.keyframe_insert("location", frame=frames)


def fit_camera(scene, cam, points: list[Vector], frames: int):
    """Binary-search the closest distance where every point stays inside the safe frame
    at the start, middle and end of the move. Guessing the distance crops diagrams."""
    from bpy_extras.object_utils import world_to_camera_view

    def fits(dist: float) -> bool:
        set_camera_path(cam, dist, frames)
        for f in (1, frames // 2, frames):
            scene.frame_set(f)
            for p in points:
                v = world_to_camera_view(scene, cam, p)
                if v.z <= 0 or not (0.04 < v.x < 0.96 and 0.07 < v.y < 0.93):
                    return False
        return True

    lo, hi = 2.0, 400.0
    for _ in range(24):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if fits(mid) else (mid, hi)
    set_camera_path(cam, hi, frames)
    scene.frame_set(1)


def build(graph: dict, a: argparse.Namespace):
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    coll = scene.collection
    fps, frames = a.fps, int(a.seconds * a.fps)
    scene.render.fps = fps
    scene.frame_start, scene.frame_end = 1, frames

    font = find_font(FONT_REGULAR)
    font_bold = find_font(FONT_BOLD) or font
    classes = graph["class_defs"]
    nodes = {n["id"]: n for n in graph["nodes"]}

    def style(n):
        s = dict(DEFAULT_CLASS)
        s.update(classes.get(n.get("cls") or "", {}))
        return s

    # Extent drives camera distance and ground size.
    xs = [n["x"] for n in nodes.values()] or [0]
    ys = [n["y"] for n in nodes.values()] or [0]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) + NODE_W
    center = Vector(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, 0.6))

    # Camera on an orbiting rig, always aimed at the diagram centre.
    target = link(bpy.data.objects.new("target", None), coll)
    target.location = center
    rig = link(bpy.data.objects.new("rig", None), coll)
    rig.location = center
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 35
    cam = link(bpy.data.objects.new("cam", cam_data), coll)
    cam.parent = rig
    tc = cam.constraints.new("TRACK_TO")
    tc.target = target
    tc.track_axis = "TRACK_NEGATIVE_Z"
    tc.up_axis = "UP_Y"
    scene.camera = cam
    rig.rotation_euler.z = math.radians(-14)
    rig.keyframe_insert("rotation_euler", index=2, frame=1)
    rig.rotation_euler.z = math.radians(14)
    rig.keyframe_insert("rotation_euler", index=2, frame=frames)

    # World, ground, light.
    world = bpy.data.worlds.new("world")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = hex_to_linear(BG)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    bpy.ops.mesh.primitive_plane_add(size=span * 6, location=(center.x, center.y, 0))
    ground = bpy.context.active_object
    ground.data.materials.append(mat_surface("ground", "#0b1118", rough=0.28, metallic=0.2))
    key = bpy.data.lights.new("key", "AREA")
    key.energy = 900 + span * 40
    key.size = span
    key.color = hex_to_linear("#cfe0ff")[:3]
    kl = link(bpy.data.objects.new("key", key), coll)
    kl.location = (center.x - span * 0.3, center.y - span * 0.3, span * 0.9)
    kl.rotation_euler = (math.radians(20), math.radians(-15), 0)

    # Timeline plan: one beat per rank for the build, then data flows.
    max_rank = max((n["rank"] for n in nodes.values()), default=0)
    beat = max(6, int(fps * 0.45))
    # With a title, give it its own beat before anything else moves.
    build_start = int(fps * (2.2 if a.title else 0.6))
    appear = {nid: build_start + n["rank"] * beat for nid, n in nodes.items()}
    flow_start = build_start + (max_rank + 1) * beat + int(fps * 0.4)

    # Subgraph platforms.
    for grp in graph["groups"]:
        members = [n for n in nodes.values() if n.get("group") == grp["id"]]
        if not members:
            continue
        gx = [m["x"] for m in members]
        gy = [m["y"] for m in members]
        z = members[0]["z"]
        w = max(gx) - min(gx) + NODE_W + 1.0
        d = max(gy) - min(gy) + NODE_D + 1.6
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=((max(gx) + min(gx)) / 2, (max(gy) + min(gy)) / 2, z - 0.08))
        plat = bpy.context.active_object
        plat.scale = (w, d, 0.16)
        bev = plat.modifiers.new("bevel", "BEVEL")
        bev.width, bev.segments = 0.06, 3
        stroke = style(members[0])["stroke"]
        plat.data.materials.append(mat_surface("platform", "#0e1a22", rough=0.2, emit=stroke, emit_strength=0.08, alpha=0.55))
        # Glowing lip so the tier reads from any angle.
        rim = bezier([Vector((plat.location.x + sx * w / 2, plat.location.y + sy * d / 2, z)) for sx, sy in
                      ((-1, -1), (1, -1), (1, 1), (-1, 1))], "rim", coll, 0.02)
        rim.data.splines[0].use_cyclic_u = True
        for bp in rim.data.splines[0].bezier_points:
            bp.handle_left_type = bp.handle_right_type = "VECTOR"
        rim.data.materials.append(mat_emit("rim", stroke, 3.0))
        title = make_text(grp["title"].upper(), font_bold, 0.42, stroke, 2.0, coll)
        title.location = (plat.location.x, plat.location.y - d / 2 - 0.1, z + 0.35)
        billboard(title, cam)
        t0 = min(appear[m["id"]] for m in members) - 6
        for ob in (plat, rim, title):
            pop_in(ob, t0)

    # Nodes. frame_points collects everything the camera must keep in shot.
    tops: dict[str, float] = {}
    frame_points: list[Vector] = []
    for nid, n in nodes.items():
        st = style(n)
        body, h = node_mesh(n["shape"], coll)
        body.location = (n["x"], n["y"], n["z"] + h / 2)
        body.data.materials.append(mat_surface("fill", st["fill"], rough=0.35, emit=st["stroke"], emit_strength=0.04))
        body.data.materials.append(mat_emit("stroke", st["stroke"], 4.0, cull_back=True))
        tops[nid] = n["z"] + h
        for sx in (-1, 1):
            for sy in (-1, 1):
                frame_points.append(Vector((n["x"] + sx * NODE_W / 2, n["y"] + sy * NODE_D / 2, n["z"])))
            frame_points.append(Vector((n["x"] + sx * NODE_W / 2, n["y"], n["z"] + h + 1.2)))
        lines = n["label"].split("\n")
        head = make_text(lines[0], font_bold, 0.55, st.get("color", "#e8eef7"), 1.2, coll, max_width=NODE_W * 1.05)
        head.location = (n["x"], n["y"], n["z"] + h + 0.8 + (0.3 if len(lines) > 1 else 0))
        billboard(head, cam)
        labels = [head]
        if len(lines) > 1:
            sub = make_text("\n".join(lines[1:]), font, 0.36, st.get("color", "#e8eef7"), 0.8, coll, max_width=NODE_W * 1.15)
            sub.location = (n["x"], n["y"], n["z"] + h + 0.52)
            billboard(sub, cam)
            labels.append(sub)
        pop_in(body, appear[nid])
        for lb in labels:
            pop_in(lb, appear[nid] + 4)

    # Edges and data pulses.
    period = int(fps * 2.2)
    for i, e in enumerate(graph["edges"]):
        s, t = nodes[e["src"]], nodes[e["dst"]]
        st = style(s)
        p_src = Vector((s["x"], s["y"], tops[e["src"]] - 0.3))
        p_dst = Vector((t["x"], t["y"], tops[e["dst"]] - 0.3))
        flat = (p_dst - p_src)
        flat.z = 0
        dist_xy = max(flat.length, 0.01)
        dirv = flat.normalized()
        a0 = p_src + dirv * 1.0
        a3 = p_dst - dirv * 1.1
        if e["back"]:
            # Feedback loop: swing out to the side and high, so it can't be mistaken for forward flow.
            side = Vector((-dirv.y, dirv.x, 0)) * (2.0 + dist_xy * 0.15)
            lift = 3.5 + dist_xy * 0.3
            pts = [a0, a0 + side * 0.7 + Vector((0, 0, lift)), (a0 + a3) / 2 + side + Vector((0, 0, lift * 1.25)),
                   a3 + side * 0.7 + Vector((0, 0, lift)), a3]
        else:
            lift = 0.5 + dist_xy * 0.12
            pts = [a0, a0.lerp(a3, 0.5) + Vector((0, 0, lift)), a3]
        depth = {"thick": 0.07, "dotted": 0.025}.get(e["style"], 0.04)
        tube = bezier(pts, f"edge{i}", coll, depth)
        frame_points.extend(pts)
        strength = 1.2 if e["style"] == "dotted" else 2.5
        tube.data.materials.append(mat_emit("edge", st["stroke"], strength))
        g0 = appear[e["src"]] + 8
        g1 = g0 + int(fps * 0.7)
        tube.data.bevel_factor_end = 0.0
        tube.data.keyframe_insert("bevel_factor_end", frame=g0)
        tube.data.bevel_factor_end = 1.0
        tube.data.keyframe_insert("bevel_factor_end", frame=g1)

        if e["arrow"]:
            tangent = (pts[-1] - pts[-2]).normalized()
            bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=depth * 3.2, depth=depth * 7, location=pts[-1])
            cone = bpy.context.active_object
            cone.rotation_mode = "QUATERNION"
            cone.rotation_quaternion = tangent.to_track_quat("Z", "Y")
            cone.data.materials.append(mat_emit("arrow", st["stroke"], strength * 1.4))
            pop_in(cone, g1 - 2)

        if e["label"]:
            mid = pts[len(pts) // 2] + Vector((0, 0, 0.35))
            lab = make_text(e["label"], font, 0.3, "#9fb3c8", 0.8, coll, max_width=3.2)
            lab.location = mid
            billboard(lab, cam)
            pop_in(lab, g1)

        # Pulses: two per edge, phase-staggered so the network never beats in unison.
        pulses = 1 if e["style"] == "dotted" else 2
        for k in range(pulses):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=depth * 2.4)
            orb = bpy.context.active_object
            bpy.ops.object.shade_smooth()
            orb.data.materials.append(mat_emit("pulse", st["stroke"], 14.0))
            orb.location = (0, 0, 0)
            fp = orb.constraints.new("FOLLOW_PATH")
            fp.target = tube
            fp.use_fixed_location = True
            phase = ((i * 7 + k * period // pulses) % period)
            start = flow_start + phase // 3
            fp.offset_factor = 0.0
            fp.keyframe_insert("offset_factor", frame=start)
            fp.offset_factor = 1.0
            fp.keyframe_insert("offset_factor", frame=start + period)
            fc = orb.animation_data.action.fcurves.find('constraints["Follow Path"].offset_factor')
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
            fc.modifiers.new("CYCLES")
            pop_in(orb, start, 1.0)

    fit_camera(scene, cam, frame_points, frames)

    if a.title:
        # Title card: fixed to the camera, fades out as the build begins.
        t = make_text(a.title, font_bold, 0.09, "#e8eef7", 1.0, coll)
        t.parent = cam
        t.location = (0, 0.1, -1.2)
        key_scale(t, 1, 1.0)
        key_scale(t, build_start - 14, 1.0)
        key_scale(t, build_start - 2, 0.0)

    # Render settings: EEVEE with bloom and screen-space reflections on the ground.
    r = scene.render
    r.engine = "BLENDER_EEVEE"
    w, h = (int(v) for v in a.res.lower().split("x"))
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    ee = scene.eevee
    ee.taa_render_samples = a.samples
    ee.use_bloom = True
    ee.bloom_threshold = 1.0
    ee.bloom_intensity = 0.06
    ee.bloom_radius = 5.0
    ee.use_ssr = True
    ee.use_gtao = True
    ee.use_soft_shadows = True
    scene.view_settings.view_transform = "AgX" if "AgX" in [
        i.identifier for i in scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
    scene.view_settings.look = "None"
    r.image_settings.file_format = "PNG"
    return scene


def main():
    a = args_after_dashdash()
    with open(a.graph, encoding="utf-8") as fh:
        graph = json.load(fh)
    scene = build(graph, a)
    if a.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save_blend))
    if a.still is not None:
        scene.frame_set(a.still)
        scene.render.filepath = os.path.abspath(a.out)
        bpy.ops.render.render(write_still=True)
    else:
        os.makedirs(a.out, exist_ok=True)
        scene.render.filepath = os.path.join(os.path.abspath(a.out), "f_")
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
