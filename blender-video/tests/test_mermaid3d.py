import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import mermaid3d as m  # noqa: E402

REPO_README = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")


def test_shapes_and_labels():
    g = m.parse("""flowchart LR
        A[rect] --> B(round)
        C([stadium]) --> D[(db)]
        E((circle)) --> F{decide}
        G["quoted<br/>two lines"]
    """)
    shapes = {n.id: n.shape for n in g.nodes.values()}
    assert shapes == {"A": "rect", "B": "round", "C": "stadium", "D": "cylinder",
                      "E": "circle", "F": "diamond", "G": "rect"}
    assert g.nodes["G"].label == "quoted\ntwo lines"


def test_edge_styles_labels_and_chains():
    g = m.parse("""graph TD
        A -->|pipe| B
        B -- inline text --> C
        C -.-> D
        D ==> E --- F
        F -.- G
    """)
    got = [(e.src, e.dst, e.label, e.style, e.arrow) for e in g.edges]
    assert got == [
        ("A", "B", "pipe", "solid", True),
        ("B", "C", "inline text", "solid", True),
        ("C", "D", "", "dotted", True),
        ("D", "E", "", "thick", True),
        ("E", "F", "", "solid", False),
        ("F", "G", "", "dotted", False),
    ]


def test_subgraph_membership_and_classes():
    g = m.parse("""flowchart TD
        subgraph API [Backend API]
            S["FastAPI"]:::svc
        end
        S --> DB[(Postgres)]
        classDef svc fill:#111,stroke:#0f0,color:#fff
    """)
    assert g.groups["API"].title == "Backend API"
    assert g.nodes["S"].group == "API"
    assert g.nodes["DB"].group is None
    assert g.nodes["S"].cls == "svc"
    assert g.class_defs["svc"]["stroke"] == "#0f0"


def test_classdef_tolerates_spaces_after_commas():
    g = m.parse("""flowchart LR
        A:::svc
        classDef svc fill:#111, stroke:#0f0 , color: #fff;
    """)
    assert g.class_defs["svc"] == {"fill": "#111", "stroke": "#0f0", "color": "#fff"}


def test_comments_and_unsupported_directives_are_skipped():
    g = m.parse("""flowchart LR
        %% a comment
        A --> B %% trailing
        style A fill:#f00
        linkStyle 0 stroke:#fff
    """)
    assert list(g.nodes) == ["A", "B"]


@pytest.mark.parametrize("src, msg", [
    ("A --> B", "header"),
    ("flowchart TD\nA[unclosed", "missing"),
    ("flowchart TD\nsubgraph X\nA", "unclosed subgraph"),
    ("flowchart TD\nend", "without subgraph"),
    ("flowchart TD\nA --> ", "node id"),
])
def test_errors_name_the_problem(src, msg):
    with pytest.raises(m.ParseError, match=msg):
        m.parse(src)


def test_last_declared_edge_closes_the_cycle():
    g = m.layout(m.parse("""flowchart LR
        A --> B --> C --> D
        D --> B
    """))
    assert [e.back for e in g.edges] == [False, False, False, True]
    assert [g.nodes[n].rank for n in "ABCD"] == [0, 1, 2, 3]


def test_layout_directions():
    src = "flowchart {}\nA --> B"
    lr = m.layout(m.parse(src.format("LR")))
    assert lr.nodes["B"].x > lr.nodes["A"].x
    td = m.layout(m.parse(src.format("TD")))
    assert td.nodes["B"].y < td.nodes["A"].y
    rl = m.layout(m.parse(src.format("RL")))
    assert rl.nodes["B"].x < rl.nodes["A"].x


def test_grouped_nodes_are_lifted_and_layout_is_centred():
    g = m.layout(m.parse("""flowchart LR
        subgraph T [tier]
            A
        end
        A --> B
    """))
    assert g.nodes["A"].z > 0 and g.nodes["B"].z == 0
    assert abs(g.nodes["A"].x + g.nodes["B"].x) < 1e-6


def test_no_two_nodes_share_a_position():
    with open(REPO_README, encoding="utf-8") as fh:
        g = m.layout(m.parse(fh.read()))
    positions = [(n.x, n.y) for n in g.nodes.values()]
    assert len(positions) == len(set(positions)) == 17
    assert sum(e.back for e in g.edges) == 1  # the CUT --> ZOOM release loop
