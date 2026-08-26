#!/usr/bin/env python3
"""Probe unrestricted two-hub Puleo reductions for delta-8 local graphs."""

from __future__ import annotations

from itertools import combinations
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csc_matrix


def edge(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)


def triangle_edges(t):
    return frozenset(edge(a, b) for a, b in combinations(t, 2))


def all_triangles(vertices: int, edges: frozenset[tuple[int, int]]):
    return tuple(t for t in combinations(range(vertices), 3) if triangle_edges(t) <= edges)


def reduction_witness(vertices: int, edges: frozenset[tuple[int, int]]):
    hubs = {0, 1}
    triangles = all_triangles(vertices, edges)
    hub_triangles = tuple(t for t in triangles if hubs.intersection(t))
    edge_tuple = tuple(sorted(edges))
    edge_index = {e: i for i, e in enumerate(edge_tuple)}
    triangle_count = len(triangles)
    variable_count = triangle_count + len(edge_tuple)
    rows = []
    lower = []
    upper = []

    def add(coefficients, lo=-np.inf, hi=np.inf):
        row = np.zeros(variable_count)
        for index, value in coefficients.items():
            row[index] = value
        rows.append(row)
        lower.append(lo)
        upper.append(hi)

    for e in edges:
        add({i: 1 for i, t in enumerate(triangles) if e in triangle_edges(t)}, hi=1)
    for t in hub_triangles:
        add({triangle_count + edge_index[e]: 1 for e in triangle_edges(t)}, lo=1)
    for i, t in enumerate(triangles):
        for e in triangle_edges(t):
            if hubs.isdisjoint(e):
                add({i: 1, triangle_count + edge_index[e]: -1}, hi=0)
    budget = {i: -2 for i in range(triangle_count)}
    budget.update({triangle_count + i: 1 for i in range(len(edge_tuple))})
    add(budget, hi=0)

    result = milp(
        c=np.zeros(variable_count),
        integrality=np.ones(variable_count),
        bounds=Bounds(np.zeros(variable_count), np.ones(variable_count)),
        constraints=LinearConstraint(csc_matrix(np.vstack(rows)), np.array(lower), np.array(upper)),
        options={"mip_rel_gap": 0.0, "presolve": True},
    )
    if not result.success:
        return None
    packing = tuple(t for i, t in enumerate(triangles) if result.x[i] > 0.5)
    cover = frozenset(e for i, e in enumerate(edge_tuple) if result.x[triangle_count + i] > 0.5)

    used = set()
    for t in packing:
        te = triangle_edges(t)
        assert te <= edges and not (used & te)
        used.update(te)
    assert len(cover) <= 2 * len(packing)
    assert all(triangle_edges(t) & cover for t in hub_triangles)
    assert all(
        e in cover
        for t in packing
        for e in triangle_edges(t)
        if hubs.isdisjoint(e)
    )
    return packing, cover


def two_hub_core(c: int, missing_core_edges=()):
    vertices = c + 2
    edges = {edge(0, 1)}
    edges.update(edge(hub, x) for hub in (0, 1) for x in range(2, vertices))
    core_edges = set(combinations(range(2, vertices), 2))
    core_edges -= {edge(a + 2, b + 2) for a, b in missing_core_edges}
    edges.update(core_edges)
    return vertices, frozenset(edges)


def main() -> int:
    cases = {
        "K7_core": two_hub_core(7),
        "K7_minus_edge_core": two_hub_core(7, ((0, 1),)),
    }
    for name, (vertices, edges) in cases.items():
        witness = reduction_witness(vertices, edges)
        print(name, "REDUCIBLE" if witness else "OBSTRUCTION")
        if witness:
            packing, cover = witness
            print(" packing_size", len(packing), packing)
            print(" cover_size", len(cover), sorted(cover))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
