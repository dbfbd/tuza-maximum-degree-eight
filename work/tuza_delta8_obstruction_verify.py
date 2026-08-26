#!/usr/bin/env python3
"""Independent exact verification of the two delta-8 codegree-four exceptions."""

from __future__ import annotations

from itertools import combinations
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).with_name("vendor")))
from z3 import Bool, If, Implies, Or, PbLe, Solver, Sum, unsat  # type: ignore

from tuza_delta8_codegree4_counts import canonical_core, core_mask_of, local_graph
from tuza_delta8_pair_probe import all_triangles, edge, triangle_edges


CASES = (
    (0, 29491, 29491),
    (0, 29491, 30037),
)


def z3_reducible(edges):
    vertices = 12
    hubs = {0, 1}
    triangles = all_triangles(vertices, edges)
    hub_triangles = tuple(t for t in triangles if hubs.intersection(t))
    edge_tuple = tuple(sorted(edges))
    s = tuple(Bool(f"s_{i}") for i in range(len(triangles)))
    x = {e: Bool(f"x_{a}_{b}") for a, b in edge_tuple for e in [(a, b)]}
    solver = Solver()
    for e in edge_tuple:
        users = [s[i] for i, t in enumerate(triangles) if e in triangle_edges(t)]
        solver.add(PbLe([(z, 1) for z in users], 1))
    for t in hub_triangles:
        solver.add(Or([x[e] for e in triangle_edges(t)]))
    for i, t in enumerate(triangles):
        for e in triangle_edges(t):
            if hubs.isdisjoint(e):
                solver.add(Implies(s[i], x[e]))
    solver.add(Sum([If(z, 1, 0) for z in x.values()]) <= 2 * Sum([If(z, 1, 0) for z in s]))
    return solver.check(), len(triangles), len(hub_triangles)


def redirected_core(edges, exclusive_vertex=6):
    u = 0
    common = sorted(
        v for v in range(12)
        if v not in (u, exclusive_vertex)
        and edge(u, v) in edges
        and edge(exclusive_vertex, v) in edges
    )
    mapping = {v: i for i, v in enumerate(common)}
    induced = frozenset(
        (mapping[a], mapping[b])
        for a, b in edges
        if a in mapping and b in mapping
    )
    return tuple(common), core_mask_of(induced), induced


def main() -> int:
    for case in CASES:
        graph = local_graph(*case)
        status, triangles, hub_triangles = z3_reducible(graph)
        print("case", case, "z3_status", status, "triangles", triangles, "hub_triangles", hub_triangles)
        assert status == unsat
        common, core, induced = redirected_core(graph)
        print(" redirect_edge", (0, 6), "common", common, "core_mask", core, "core_edges", sorted(induced))
        assert len(common) == 4
        assert len(induced) == 5
        assert canonical_core(core) == 31  # K4 minus one edge, up to relabelling.
    print("ALL TWO OBSTRUCTIONS AND REDIRECTIONS VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
