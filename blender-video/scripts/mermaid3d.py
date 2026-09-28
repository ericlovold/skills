"""Parse a Mermaid flowchart and lay it out for a 3D scene.

Pure Python, no Blender import, so it runs (and is tested) anywhere.
build_scene.py runs inside Blender and consumes the JSON this module writes.

Supported Mermaid subset (enough for architecture diagrams):
  flowchart|graph TD|TB|BT|LR|RL
  node shapes   A[rect] A(round) A([stadium]) A[(cylinder)] A((circle)) A{diamond}
  labels        quoted or bare, <br/> becomes a line break
  edges         -->  ---  -.->  -.-  ==>  with |label| or -- label -->, chains A --> B --> C
  groups        subgraph ID [Title] ... end   (nesting flattens to the innermost group)
  styling       classDef name fill:#hex,stroke:#hex,color:#hex   and   A:::name
  comments      %% ...

Usage:
  python mermaid3d.py diagram.mmd -o graph.json
  python mermaid3d.py README.md -o graph.json      # first ```mermaid block
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field

# Order matters: longer delimiters must be tried before their prefixes.
SHAPES = [
    ("([", "])", "stadium"),
    ("[(", ")]", "cylinder"),
    ("((", "))", "circle"),
    ("[", "]", "rect"),
    ("(", ")", "round"),
    ("{", "}", "diamond"),
]

# An edge operator, optionally with a -- text --> style inline label.
EDGE_RE = re.compile(
    r"""\s*(?:
        (?P<txt_open>--|-\.|==)\s+(?P<txt>[^-=.>|][^>]*?)\s+(?P<txt_close>-->|-\.->|==>|---)
      | (?P<op>-\.->|-\.-|==>|-->|---)
    )\s*(?:\|(?P<pipe>[^|]*)\|)?\s*""",
    re.VERBOSE,
)
ID_RE = re.compile(r"[A-Za-z_][\w-]*")
CLASS_SUFFIX_RE = re.compile(r":::([\w-]+)")


@dataclass
class Node:
    id: str
    label: str
    shape: str = "rect"
    cls: str | None = None
    group: str | None = None
    rank: int = 0
    order: int = 0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Edge:
    src: str
    dst: str
    label: str = ""
    style: str = "solid"  # solid | dotted | thick
    arrow: bool = True
    back: bool = False  # True when the edge closes a cycle (drawn, but ignored by ranking)


@dataclass
class Group:
    id: str
    title: str
    parent: str | None = None


@dataclass
class Graph:
    direction: str = "TD"
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    groups: dict[str, Group] = field(default_factory=dict)
    class_defs: dict[str, dict[str, str]] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "direction": self.direction,
            "nodes": [asdict(n) for n in self.nodes.values()],
            "edges": [asdict(e) for e in self.edges],
            "groups": [asdict(g) for g in self.groups.values()],
            "class_defs": self.class_defs,
        }


class ParseError(ValueError):
    pass


def extract_mermaid(text: str) -> str:
    """Return the first ```mermaid fenced block, or the text itself if there is none."""
    m = re.search(r"```mermaid\s*\n(.*?)```", text, re.DOTALL)
    return m.group(1) if m else text


def _clean_label(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        raw = raw[1:-1]
    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    return raw.strip()


def _read_node(s: str, pos: int) -> tuple[str, str | None, str | None, str | None, int]:
    """Read `ID`, optional shape+label, optional :::class starting at pos.

    Returns (id, label, shape, cls, new_pos). label/shape are None for a bare reference.
    """
    m = ID_RE.match(s, pos)
    if not m:
        raise ParseError(f"expected a node id at: {s[pos:]!r}")
    node_id, pos = m.group(0), m.end()
    label = shape = None
    for open_, close, name in SHAPES:
        if s.startswith(open_, pos):
            end = _find_close(s, pos + len(open_), close)
            label, shape, pos = _clean_label(s[pos + len(open_):end]), name, end + len(close)
            break
    cls = None
    cm = CLASS_SUFFIX_RE.match(s, pos)
    if cm:
        cls, pos = cm.group(1), cm.end()
    return node_id, label, shape, cls, pos


def _find_close(s: str, start: int, close: str) -> int:
    """Find the closing delimiter, skipping over a quoted label."""
    i = start
    if i < len(s) and s[i] == '"':
        q = s.find('"', i + 1)
        if q == -1:
            raise ParseError(f"unterminated quote in: {s!r}")
        i = q + 1
    end = s.find(close, i)
    if end == -1:
        raise ParseError(f"missing {close!r} in: {s!r}")
    return end


def _style_of(op: str) -> tuple[str, bool]:
    if op.startswith("-."):
        return "dotted", op.endswith(">")
    if op.startswith("=="):
        return "thick", True
    return "solid", op.endswith(">")


def parse(text: str) -> Graph:
    g = Graph()
    group_stack: list[str] = []
    header_seen = False

    def touch(node_id, label, shape, cls):
        node = g.nodes.get(node_id)
        if node is None:
            node = g.nodes[node_id] = Node(id=node_id, label=label or node_id)
            node.group = group_stack[-1] if group_stack else None
        if label is not None:
            node.label, node.shape = label, shape
            # A node is owned by the group where it is first *defined* with a shape.
            node.group = group_stack[-1] if group_stack else node.group
        if cls:
            node.cls = cls

    for lineno, raw in enumerate(extract_mermaid(text).splitlines(), 1):
        line = raw.split("%%", 1)[0].strip().rstrip(";")
        if not line:
            continue
        if not header_seen:
            m = re.match(r"(flowchart|graph)\s+(TD|TB|BT|LR|RL)\b", line)
            if not m:
                raise ParseError(f"line {lineno}: expected 'flowchart TD' style header, got {line!r}")
            g.direction = "TD" if m.group(2) == "TB" else m.group(2)
            header_seen = True
            continue
        if line.startswith("classDef "):
            _, name, props = line.split(None, 2)
            g.class_defs[name] = dict(
                p.split(":", 1) for p in props.rstrip(";").split(",") if ":" in p
            )
            continue
        if line.startswith("class "):
            _, ids, cls = line.split(None, 2)
            for nid in ids.split(","):
                touch(nid.strip(), None, None, cls.strip())
            continue
        if re.match(r"(style|linkStyle|click|direction)\b", line):
            continue  # presentation hints with no 3D meaning yet
        m = re.match(r"subgraph\s+(\S+?)(?:\s*\[(.*)\])?\s*$", line)
        if m:
            gid = m.group(1)
            title = _clean_label(m.group(2)) if m.group(2) else gid
            g.groups[gid] = Group(gid, title, group_stack[-1] if group_stack else None)
            group_stack.append(gid)
            continue
        if line == "end":
            if not group_stack:
                raise ParseError(f"line {lineno}: 'end' without subgraph")
            group_stack.pop()
            continue

        try:
            nid, label, shape, cls, pos = _read_node(line, 0)
            touch(nid, label, shape, cls)
            prev = nid
            while pos < len(line):
                em = EDGE_RE.match(line, pos)
                if not em:
                    raise ParseError(f"unexpected text {line[pos:]!r}")
                op = em.group("op") or em.group("txt_close")
                edge_label = em.group("pipe") or em.group("txt") or ""
                style, arrow = _style_of(op)
                nid, label, shape, cls, pos = _read_node(line, em.end())
                touch(nid, label, shape, cls)
                g.edges.append(Edge(prev, nid, _clean_label(edge_label), style, arrow))
                prev = nid
        except ParseError as exc:
            raise ParseError(f"line {lineno}: {exc}") from None

    if not header_seen:
        raise ParseError("no flowchart header found")
    if group_stack:
        raise ParseError(f"unclosed subgraph {group_stack[-1]!r}")
    return g


# ---------------------------------------------------------------- layout


def _mark_back_edges(g: Graph) -> None:
    """Add edges in declaration order; an edge that would close a cycle is a back edge.

    Authors write the main flow first and the loop-closing edge last (CUT --> ZOOM),
    so declaration order picks the edge a reader would call "the way back".
    O(E * (V + E)), fine for diagrams a human can read.
    """
    out: dict[str, list[str]] = {n: [] for n in g.nodes}

    def reaches(a: str, b: str) -> bool:
        seen, stack = {a}, [a]
        while stack:
            n = stack.pop()
            if n == b:
                return True
            for m in out[n]:
                if m not in seen:
                    seen.add(m)
                    stack.append(m)
        return False

    for e in g.edges:
        if e.src == e.dst or reaches(e.dst, e.src):
            e.back = True
        else:
            out[e.src].append(e.dst)


def layout(g: Graph, rank_gap: float = 4.0, lane_gap: float = 3.2, group_lift: float = 1.2) -> Graph:
    """Layered layout on the ground plane.

    rank (longest path from a source) runs along the flow axis, nodes inside a rank
    spread along the cross axis, and each subgraph is lifted so groups read as tiers.
    Coordinates: flow axis is -y for TD (away from a camera looking down +y), +x for LR.
    """
    _mark_back_edges(g)
    forward = [e for e in g.edges if not e.back and e.src != e.dst]

    # Longest-path ranking over the DAG of forward edges (Kahn order).
    indeg = {n: 0 for n in g.nodes}
    for e in forward:
        indeg[e.dst] += 1
    queue = [n for n in g.nodes if indeg[n] == 0]
    for n in g.nodes.values():
        n.rank = 0
    while queue:
        n = queue.pop(0)
        for e in forward:
            if e.src == n:
                g.nodes[e.dst].rank = max(g.nodes[e.dst].rank, g.nodes[n].rank + 1)
                indeg[e.dst] -= 1
                if indeg[e.dst] == 0:
                    queue.append(e.dst)

    ranks: dict[int, list[Node]] = {}
    for n in g.nodes.values():  # declaration order is the initial order
        ranks.setdefault(n.rank, []).append(n)

    # Barycenter sweeps: order each rank by the mean position of its neighbours,
    # keeping group members adjacent so platforms stay compact.
    group_index = {gid: i for i, gid in enumerate(g.groups)}
    neighbours: dict[str, list[str]] = {n: [] for n in g.nodes}
    for e in forward:
        neighbours[e.src].append(e.dst)
        neighbours[e.dst].append(e.src)
    for sweep in range(6):
        pos = {n.id: i for r in ranks.values() for i, n in enumerate(r)}
        order = sorted(ranks) if sweep % 2 == 0 else sorted(ranks, reverse=True)
        for r in order:
            def key(n: Node) -> tuple:
                nb = [pos[m] for m in neighbours[n.id]]
                bary = sum(nb) / len(nb) if nb else pos[n.id]
                return (group_index.get(n.group, -1), bary)
            ranks[r].sort(key=key)

    flip = g.direction in ("BT", "RL")
    max_rank = max(ranks) if ranks else 0
    for r, members in ranks.items():
        rr = (max_rank - r) if flip else r
        width = (len(members) - 1) * lane_gap
        for i, n in enumerate(members):
            n.order = i
            flow = rr * rank_gap
            cross = i * lane_gap - width / 2
            if g.direction in ("LR", "RL"):
                n.x, n.y = flow, -cross
            else:
                n.x, n.y = cross, -flow
            n.z = group_lift if n.group else 0.0

    # Centre the whole diagram on the origin so the camera can orbit it.
    if g.nodes:
        xs = [n.x for n in g.nodes.values()]
        ys = [n.y for n in g.nodes.values()]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        for n in g.nodes.values():
            n.x, n.y = round(n.x - cx, 4), round(n.y - cy, 4)
    return g


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help=".mmd file, or a Markdown file containing a ```mermaid block")
    ap.add_argument("-o", "--out", help="write layout JSON here (default: stdout)")
    ap.add_argument("--direction", choices=["TD", "BT", "LR", "RL"],
                    help="override the diagram's direction (LR suits 16:9, TD suits 9:16)")
    ap.add_argument("--rank-gap", type=float, default=4.5, help="distance between flow steps")
    ap.add_argument("--lane-gap", type=float, default=3.8, help="distance between siblings")
    args = ap.parse_args(argv)
    with open(args.source, encoding="utf-8") as fh:
        g = parse(fh.read())
    if args.direction:
        g.direction = args.direction
    g = layout(g, rank_gap=args.rank_gap, lane_gap=args.lane_gap)
    data = json.dumps(g.to_json(), indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(data + "\n")
    else:
        print(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
