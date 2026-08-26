#!/usr/bin/env python3
"""Count codegree-four side configurations for the 8-regular boundary case."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from itertools import combinations, permutations
import json
from pathlib import Path
import subprocess

from tuza_delta8_link_census import N, parse_graph6, wke_witness
from tuza_delta8_pair_probe import edge


C = tuple(range(4))
A = tuple(range(3))
CORE_PAIRS = tuple(combinations(C, 2))
CORE_INDEX = {e: i for i, e in enumerate(CORE_PAIRS)}
CORE_PERMS = tuple(permutations(C))
A_PERMS = tuple(permutations(A))
SIDE_PAIRS = tuple((4 + a, c) for a in A for c in C) + tuple((4 + a, 4 + b) for a, b in combinations(A, 2))
SIDE_INDEX = {e: i for i, e in enumerate(SIDE_PAIRS)}


def core_mask_of(edges):
    return sum(1 << CORE_INDEX[tuple(sorted(e))] for e in edges)


def core_edges_of(mask):
    return frozenset(e for i, e in enumerate(CORE_PAIRS) if (mask >> i) & 1)


def side_edges_of(mask):
    return frozenset(e for i, e in enumerate(SIDE_PAIRS) if (mask >> i) & 1)


def permute_core(mask, p):
    return core_mask_of(tuple(sorted((p[a], p[b]))) for a, b in core_edges_of(mask))


def permute_side(side, p, q):
    image = 0
    for x, y in side_edges_of(side):
        if x >= 4 and y >= 4:
            e = tuple(sorted((4 + q[x - 4], 4 + q[y - 4])))
        else:
            e = (4 + q[x - 4], p[y])
        image |= 1 << SIDE_INDEX[e]
    return image


def canonical_core(mask):
    return min(permute_core(mask, p) for p in CORE_PERMS)


def canonical_images(core, side):
    target = canonical_core(core)
    return target, {
        permute_side(side, p, q)
        for p in CORE_PERMS
        if permute_core(core, p) == target
        for q in A_PERMS
    }


IDENTITY_C = tuple(C)


def normalize_exclusive(side):
    return min(permute_side(side, IDENTITY_C, q) for q in A_PERMS)


def core_automorphisms(core):
    return tuple(p for p in CORE_PERMS if permute_core(core, p) == core)


def canonical_pair(core, left, right):
    return min(
        tuple(sorted((normalize_exclusive(permute_side(left, p, A_PERMS[0])),
                      normalize_exclusive(permute_side(right, p, A_PERMS[0])))))
        for p in core_automorphisms(core)
    )


def extract_configuration(edges, distinguished):
    core_vertices = sorted(v for v in range(N) if v != distinguished and edge(v, distinguished) in edges)
    assert len(core_vertices) == 4
    exclusive = sorted(v for v in range(N) if v != distinguished and v not in core_vertices)
    assert len(exclusive) == 3
    cm = {v: i for i, v in enumerate(core_vertices)}
    am = {v: i for i, v in enumerate(exclusive)}
    core = core_mask_of((cm[a], cm[b]) for a, b in edges if a in cm and b in cm)
    side = 0
    for a, b in edges:
        if a in am and b in cm:
            side |= 1 << SIDE_INDEX[4 + am[a], cm[b]]
        elif b in am and a in cm:
            side |= 1 << SIDE_INDEX[4 + am[b], cm[a]]
        elif a in am and b in am:
            e = tuple(sorted((4 + am[a], 4 + am[b])))
            side |= 1 << SIDE_INDEX[e]
    return core, side


def boundary_degrees(side):
    answer = [0] * 4
    for x, y in side_edges_of(side):
        if x >= 4 and y < 4:
            answer[y] += 1
    return tuple(answer)


def compatible(core_degrees, left_degrees, right_degrees):
    return all(a + b + c <= 6 for a, b, c in zip(core_degrees, left_degrees, right_degrees))


def local_graph(core, left, right):
    # u=0, v=1, C=2..5, A=6..8, B=9..11.
    answer = {edge(0, 1)}
    answer.update(edge(h, x + 2) for h in (0, 1) for x in C)
    answer.update(edge(0, a) for a in (6, 7, 8))
    answer.update(edge(1, b) for b in (9, 10, 11))
    answer.update(edge(a + 2, b + 2) for a, b in core_edges_of(core))

    def add_side(mask, exclusive):
        for x, y in side_edges_of(mask):
            if x >= 4 and y >= 4:
                answer.add(edge(exclusive[x - 4], exclusive[y - 4]))
            else:
                answer.add(edge(exclusive[x - 4], y + 2))

    add_side(left, (6, 7, 8))
    add_side(right, (9, 10, 11))
    return frozenset(answer)


def main(args) -> int:
    root = Path(__file__).resolve().parent
    geng = root / "nauty" / "geng.exe"
    result = subprocess.run([str(geng), "-cq", "8"], check=True, stdout=subprocess.PIPE, text=True)
    allowed = defaultdict(set)
    embeddings = 0
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        graph = parse_graph6(line.strip())
        if wke_witness(graph) is not None:
            continue
        degrees = [sum(v in e for e in graph) for v in range(N)]
        for r, degree in enumerate(degrees):
            if degree != 4:
                continue
            core, side = extract_configuration(graph, r)
            canonical, images = canonical_images(core, side)
            allowed[canonical].update(images)
            embeddings += 1

    print("non_WKE_degree4_link_embeddings", embeddings)
    print("canonical_cores", len(allowed))
    total_raw_pairs = 0
    total_pair_orbits = 0
    all_pair_orbits = []
    for core in sorted(allowed):
        sides = sorted({normalize_exclusive(side) for side in allowed[core]})
        side_degrees = {side: boundary_degrees(side) for side in sides}
        core_degrees = tuple(sum(v in e for e in core_edges_of(core)) for v in C)
        compatible_raw = [
            (left, right)
            for i, left in enumerate(sides)
            for right in sides[i:]
            if compatible(core_degrees, side_degrees[left], side_degrees[right])
        ]
        pair_orbits = {canonical_pair(core, left, right) for left, right in compatible_raw}
        all_pair_orbits.extend((core, left, right) for left, right in sorted(pair_orbits))
        total_raw_pairs += len(compatible_raw)
        total_pair_orbits += len(pair_orbits)
        print(
            "CORE", core,
            "core_edges", len(core_edges_of(core)),
            "exclusive_orbit_sides", len(sides),
            "compatible_pairs_before_core_quotient", len(compatible_raw),
            "pair_orbits", len(pair_orbits),
            flush=True,
        )
    print("total_exclusive_orbit_sides", sum(len({normalize_exclusive(x) for x in s}) for s in allowed.values()))
    print("total_compatible_before_core_quotient", total_raw_pairs)
    print("total_pair_orbits", total_pair_orbits)
    if args.pairs_output:
        Path(args.pairs_output).write_text(
            json.dumps(
                [{"core": core, "left": left, "right": right} for core, left, right in all_pair_orbits],
                indent=2,
            ),
            encoding="utf-8",
        )
        print("pairs_written", args.pairs_output)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs-output")
    raise SystemExit(main(parser.parse_args()))
