#!/usr/bin/env python3
"""Independent nauty census of connected 8-vertex links of maximum degree 4."""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from pathlib import Path
import subprocess


N = 8
VERTICES = tuple(range(N))
ALL_PAIRS = tuple((i, j) for j in range(1, N) for i in range(j))


def parse_graph6(line: str) -> frozenset[tuple[int, int]]:
    data = [ord(c) - 63 for c in line.strip()]
    assert data and data[0] == N
    bits = []
    for value in data[1:]:
        bits.extend((value >> shift) & 1 for shift in range(5, -1, -1))
    return frozenset(edge for edge, present in zip(ALL_PAIRS, bits) if present)


def all_matchings(edges: tuple[tuple[int, int], ...]):
    answer = []

    def rec(start, chosen, used):
        answer.append(tuple(chosen))
        for i in range(start, len(edges)):
            a, b = edges[i]
            if a not in used and b not in used:
                rec(i + 1, chosen + [edges[i]], used | {a, b})

    rec(0, [], set())
    return answer


def wke_witness(edges: frozenset[tuple[int, int]]):
    edge_tuple = tuple(sorted(edges))
    for matching in all_matchings(edge_tuple):
        remainder = set(edges) - set(matching)
        for qsize in range(len(matching) + 1):
            for qtuple in combinations(VERTICES, qsize):
                q = set(qtuple)
                if all(a in q or b in q for a, b in remainder):
                    return matching, qtuple
    return None


def main() -> int:
    root = Path(__file__).resolve().parent
    geng = root / "nauty" / "geng.exe"
    if not geng.exists():
        raise SystemExit(f"missing {geng}")
    result = subprocess.run(
        [str(geng), "-cq", "-D4", str(N)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lines = tuple(line.strip() for line in result.stdout.splitlines() if line.strip())
    non_wke = []
    degree_sequences = Counter()
    high_counts = Counter()
    for graph6 in lines:
        edges = parse_graph6(graph6)
        if wke_witness(edges) is not None:
            continue
        degrees = tuple(sorted((sum(v in e for e in edges) for v in VERTICES), reverse=True))
        non_wke.append((graph6, edges, degrees))
        degree_sequences[degrees] += 1
        high_counts[sum(d >= 4 for d in degrees)] += 1

    assert len(lines) == 1929
    assert non_wke
    minimum_high = min(high_counts)
    minimum_maximum = min(ds[0] for ds in degree_sequences)
    print("connected_unlabelled_max_degree_4", len(lines))
    print("connected_non_WKE", len(non_wke))
    print("minimum_possible_max_degree", minimum_maximum)
    print("minimum_vertices_degree_at_least_4", minimum_high)
    print("high_count_histogram", dict(sorted(high_counts.items())))
    print("degree_sequence_histogram")
    for sequence, count in sorted(degree_sequences.items(), key=lambda item: (item[0], item[1])):
        print(" ", sequence, count)
    print("minimum_examples")
    for graph6, edges, degrees in non_wke:
        if sum(d >= 4 for d in degrees) == minimum_high:
            print(" ", graph6, degrees, sorted(edges))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
