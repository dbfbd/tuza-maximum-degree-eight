#!/usr/bin/env python3
"""Test the delta-8 two-hub template on every non-WKE 8-vertex link.

For an edge uv of codegree c in an 8-regular graph, the link of u contains
the vertex v of degree c. Deleting v leaves the common-neighbour core H.
The old packing/cover template generalizes with forced-edge term
t = 1 + 2(7-c) = 15-2c. This script tests that template exactly for every
possible connected non-WKE link and every distinguished vertex of degree
c in {5,6,7}.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).with_name("vendor")))
from z3 import Bool, If, Implies, Or, Solver, Sum, sat  # type: ignore

from tuza_delta8_link_census import N, parse_graph6, wke_witness


def template_witness(core_edges: frozenset[tuple[int, int]], c: int, forced_term: int | None = None):
    edges = tuple(sorted(core_edges))
    r = tuple(Bool(f"r_{c}_{i}") for i in range(len(edges)))
    q = tuple(Bool(f"q_{c}_{v}") for v in range(c))
    center = tuple(Bool(f"z_{c}_{v}") for v in range(c))
    left = tuple(Bool(f"l_{c}_{i}") for i in range(len(edges)))
    right = tuple(Bool(f"h_{c}_{i}") for i in range(len(edges)))
    solver = Solver()

    # Q covers H-R.
    for i, (a, b) in enumerate(edges):
        solver.add(Or(r[i], q[a], q[b]))
        solver.add(Implies(left[i], r[i]))
        solver.add(Implies(right[i], r[i]))

    # Edge-disjointness of uvx, uxy and vxy triangles.
    solver.add(Sum([If(z, 1, 0) for z in center]) <= 1)
    for vertex in range(c):
        solver.add(
            If(center[vertex], 1, 0)
            + Sum([If(left[i], 1, 0) for i, e in enumerate(edges) if vertex in e])
            <= 1
        )
        solver.add(
            If(center[vertex], 1, 0)
            + Sum([If(right[i], 1, 0) for i, e in enumerate(edges) if vertex in e])
            <= 1
        )
    for i in range(len(edges)):
        solver.add(If(left[i], 1, 0) + If(right[i], 1, 0) <= 1)

    packing_size = Sum(
        [If(z, 1, 0) for z in center]
        + [If(z, 1, 0) for z in left]
        + [If(z, 1, 0) for z in right]
    )
    t = 15 - 2 * c if forced_term is None else forced_term
    solver.add(t + Sum([If(z, 1, 0) for z in r]) + 2 * Sum([If(z, 1, 0) for z in q]) <= 2 * packing_size)
    if solver.check() != sat:
        return None
    model = solver.model()
    chosen_r = tuple(edges[i] for i, z in enumerate(r) if bool(model.eval(z)))
    chosen_q = tuple(v for v, z in enumerate(q) if bool(model.eval(z)))
    packing = []
    packing.extend(("uv", v) for v, z in enumerate(center) if bool(model.eval(z)))
    packing.extend(("u", edges[i]) for i, z in enumerate(left) if bool(model.eval(z)))
    packing.extend(("v", edges[i]) for i, z in enumerate(right) if bool(model.eval(z)))
    assert t + len(chosen_r) + 2 * len(chosen_q) <= 2 * len(packing)
    return chosen_r, chosen_q, tuple(packing)


def relabel_core(edges, distinguished: int):
    core_vertices = sorted(v for v in range(N) if v != distinguished and tuple(sorted((v, distinguished))) in edges)
    mapping = {v: i for i, v in enumerate(core_vertices)}
    core = frozenset(
        tuple(sorted((mapping[a], mapping[b])))
        for a, b in edges
        if a in mapping and b in mapping
    )
    return core_vertices, core


def main() -> int:
    root = Path(__file__).resolve().parent
    geng = root / "nauty" / "geng.exe"
    result = subprocess.run(
        [str(geng), "-cq", str(N)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lines = tuple(line.strip() for line in result.stdout.splitlines() if line.strip())
    assert len(lines) == 11117

    non_wke = []
    for graph6 in lines:
        edges = parse_graph6(graph6)
        if wke_witness(edges) is None:
            non_wke.append((graph6, edges))
    print("connected_unlabelled", len(lines))
    print("connected_non_WKE", len(non_wke))

    cache = {}
    embeddings = Counter()
    failures = {5: [], 6: [], 7: []}
    successes = Counter()
    for graph6, edges in non_wke:
        degrees = [sum(v in e for e in edges) for v in range(N)]
        for r, c in enumerate(degrees):
            if c not in failures:
                continue
            core_vertices, core = relabel_core(edges, r)
            assert len(core_vertices) == c
            key = (c, core)
            if key not in cache:
                cache[key] = template_witness(core, c)
            embeddings[c] += 1
            if cache[key] is None:
                failures[c].append(
                    {
                        "graph6": graph6,
                        "distinguished": r,
                        "degrees": tuple(sorted(degrees, reverse=True)),
                        "core_vertices": tuple(core_vertices),
                        "core_edges": tuple(sorted(core)),
                    }
                )
            else:
                successes[c] += 1

    print("distinguished_embeddings", dict(embeddings))
    print("template_successes", dict(successes))
    for c in (5, 6, 7):
        print(f"codegree_{c}_template_failures", len(failures[c]))
        by_core = Counter(tuple(item["core_edges"]) for item in failures[c])
        print(f"codegree_{c}_distinct_labelled_cores", len(by_core))
        for item in failures[c][:20]:
            print(" FAILURE", c, item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
