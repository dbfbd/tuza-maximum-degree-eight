#!/usr/bin/env python3
"""Independent, optimizer-free verifier for the delta-8 certificate catalogue.

This file deliberately does not import any search or MILP module.  It rebuilds
each labelled local graph from the compact orbit record, then checks the finite
Puleo-reduction certificate using only Python set operations.
"""

from __future__ import annotations

import argparse
from itertools import combinations
import json
from pathlib import Path


def edge(a: int, b: int) -> tuple[int, int]:
    assert a != b
    return (a, b) if a < b else (b, a)


def decoded_edges(vertex_count: int, mask: int):
    pairs = tuple(combinations(range(vertex_count), 2))
    assert mask >= 0 and mask < (1 << len(pairs))
    return frozenset(e for i, e in enumerate(pairs) if (mask >> i) & 1)


def decoded_side_edges(c: int, s: int, mask: int):
    pairs = tuple((c + a, v) for a in range(s) for v in range(c)) + tuple(
        (c + a, c + b) for a, b in combinations(range(s), 2)
    )
    assert mask >= 0 and mask < (1 << len(pairs))
    return frozenset(e for i, e in enumerate(pairs) if (mask >> i) & 1)


def local_graph(record):
    c = record["c"]
    sl = record["s_left"]
    sr = record["s_right"]
    cstart = 2
    astart = cstart + c
    bstart = astart + sl
    graph = {edge(0, 1)}
    graph.update(edge(h, cstart + x) for h in (0, 1) for x in range(c))
    graph.update(edge(0, astart + a) for a in range(sl))
    graph.update(edge(1, bstart + b) for b in range(sr))
    graph.update(edge(cstart + a, cstart + b) for a, b in decoded_edges(c, record["core"]))

    def add_side(s, mask, start):
        for x, y in decoded_side_edges(c, s, mask):
            if x >= c and y >= c:
                graph.add(edge(start + x - c, start + y - c))
            else:
                graph.add(edge(start + x - c, cstart + y))

    add_side(sl, record["left"], astart)
    add_side(sr, record["right"], bstart)
    return 2 + c + sl + sr, frozenset(graph)


def triangle_edges(triangle):
    assert len(triangle) == 3 and len(set(triangle)) == 3
    return frozenset(edge(a, b) for a, b in combinations(triangle, 2))


def graph_triangles(vertices, graph):
    return tuple(t for t in combinations(range(vertices), 3) if triangle_edges(t) <= graph)


def verify_witness(record, witness):
    vertices, graph = local_graph(record)
    packing = tuple(tuple(t) for t in witness["packing"])
    cover = frozenset(edge(*e) for e in witness["cover"])
    assert len(cover) == len(witness["cover"]), "duplicate cover edge"
    assert cover <= graph, "cover contains a non-edge"

    used = set()
    for triangle in packing:
        te = triangle_edges(triangle)
        assert all(0 <= v < vertices for v in triangle), "packing vertex out of range"
        assert te <= graph, "packing contains a non-triangle"
        assert not (used & te), "packing triangles share an edge"
        used.update(te)

    assert len(cover) <= 2 * len(packing), "cover exceeds twice the packing"
    hubs = {0, 1}
    for triangle in graph_triangles(vertices, graph):
        te = triangle_edges(triangle)
        if hubs.intersection(triangle):
            assert te & cover, "hub triangle is uncovered"
    for triangle in packing:
        for e in triangle_edges(triangle):
            if hubs.isdisjoint(e):
                assert e in cover, "packing boundary edge is absent from cover"


def main(args) -> int:
    records = json.loads(Path(args.pairs).read_text(encoding="utf-8"))
    witnesses = {}
    obstructions = {}
    checked = 0
    for filename in args.certificates:
        data = json.loads(Path(filename).read_text(encoding="utf-8"))
        checked += data["checked"]
        for witness in data["witnesses"]:
            index = witness["index"]
            assert index not in witnesses and index not in obstructions
            witnesses[index] = witness
        for obstruction in data["obstructions"]:
            index = obstruction["index"]
            assert index not in witnesses and index not in obstructions
            assert obstruction | {"index": index} == {"index": index, **records[index]}
            obstructions[index] = obstruction

    assert checked == len(records)
    assert set(witnesses) | set(obstructions) == set(range(len(records)))
    for number, index in enumerate(sorted(witnesses), 1):
        verify_witness(records[index], witnesses[index])
        if number % 5000 == 0:
            print("verified", number, "/", len(witnesses), flush=True)
    print("records", len(records))
    print("verified_witnesses", len(witnesses))
    print("obstruction_indices", sorted(obstructions))
    print("ALL SAVED CERTIFICATES VERIFIED WITHOUT AN OPTIMIZER")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", default="work/tuza_delta8_mixed_pairs.json")
    parser.add_argument("certificates", nargs="+")
    raise SystemExit(main(parser.parse_args()))
