#!/usr/bin/env python3
"""Build all asymmetric local-pair orbits with one degree-8 endpoint.

The distinguished edge has codegree c>=4.  The degree-8 endpoint has
s_left=7-c exclusive neighbours; the other endpoint may have any number
s_right in 0..s_left.  Both endpoint links are required to be connected and
non-WKE, as in a minimal counterexample of maximum degree eight.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from functools import cache
from itertools import combinations, permutations
import json
from pathlib import Path
import subprocess

from tuza_delta8_pair_probe import edge
from tuza_delta8_template_census import template_witness


def parse_graph6(line: str):
    data = [ord(ch) - 63 for ch in line.strip()]
    n = data[0]
    assert 0 <= n <= 62
    bits = []
    for value in data[1:]:
        bits.extend((value >> shift) & 1 for shift in range(5, -1, -1))
    pairs = tuple((i, j) for j in range(1, n) for i in range(j))
    return n, frozenset(e for e, present in zip(pairs, bits) if present)


def all_matchings(edges):
    answer = []

    def rec(start, chosen, used):
        answer.append(tuple(chosen))
        for i in range(start, len(edges)):
            a, b = edges[i]
            if a not in used and b not in used:
                rec(i + 1, chosen + [edges[i]], used | {a, b})

    rec(0, [], set())
    return answer


def is_wke(n, edges):
    edge_tuple = tuple(sorted(edges))
    for matching in all_matchings(edge_tuple):
        remainder = set(edges) - set(matching)
        for qsize in range(len(matching) + 1):
            for qtuple in combinations(range(n), qsize):
                q = set(qtuple)
                if all(a in q or b in q for a, b in remainder):
                    return True
    return False


@cache
def core_pairs(c):
    return tuple(combinations(range(c), 2))


def core_mask_of(c, edges):
    index = {e: i for i, e in enumerate(core_pairs(c))}
    return sum(1 << index[tuple(sorted(e))] for e in edges)


def core_edges_of(c, mask):
    return frozenset(e for i, e in enumerate(core_pairs(c)) if (mask >> i) & 1)


@cache
def core_perms(c):
    return tuple(permutations(range(c)))


def permute_core(c, mask, p):
    return core_mask_of(c, ((p[a], p[b]) for a, b in core_edges_of(c, mask)))


@cache
def canonical_core_data(c, mask):
    images = [(permute_core(c, mask, p), p) for p in core_perms(c)]
    target = min(image for image, _ in images)
    return target, tuple(p for image, p in images if image == target)


@cache
def automorphisms(c, core):
    return tuple(p for p in core_perms(c) if permute_core(c, core, p) == core)


@cache
def exclusive_perms(s):
    return tuple(permutations(range(s))) if s else ((),)


@cache
def side_pairs(c, s):
    return tuple((c + a, v) for a in range(s) for v in range(c)) + tuple(
        (c + a, c + b) for a, b in combinations(range(s), 2)
    )


def side_mask_of(c, s, edges):
    index = {e: i for i, e in enumerate(side_pairs(c, s))}
    return sum(1 << index[e] for e in edges)


def side_edges_of(c, s, mask):
    return frozenset(e for i, e in enumerate(side_pairs(c, s)) if (mask >> i) & 1)


def permute_side(c, s, mask, p, q):
    image = []
    for x, y in side_edges_of(c, s, mask):
        if x >= c and y >= c:
            image.append(tuple(sorted((c + q[x - c], c + q[y - c]))))
        else:
            image.append((c + q[x - c], p[y]))
    return side_mask_of(c, s, image)


def normalize_exclusive(c, s, side):
    identity = tuple(range(c))
    return min(permute_side(c, s, side, identity, q) for q in exclusive_perms(s))


def canonical_side_images(c, s, core, side):
    target, mappings = canonical_core_data(c, core)
    return target, {
        normalize_exclusive(c, s, permute_side(c, s, side, p, exclusive_perms(s)[0]))
        for p in mappings
    }


def extract_configuration(n, edges, distinguished, c):
    core_vertices = sorted(v for v in range(n) if v != distinguished and edge(v, distinguished) in edges)
    assert len(core_vertices) == c
    exclusive = sorted(v for v in range(n) if v != distinguished and v not in core_vertices)
    s = len(exclusive)
    cm = {v: i for i, v in enumerate(core_vertices)}
    am = {v: i for i, v in enumerate(exclusive)}
    core = core_mask_of(c, ((cm[a], cm[b]) for a, b in edges if a in cm and b in cm))
    abstract_side = []
    for a, b in edges:
        if a in am and b in cm:
            abstract_side.append((c + am[a], cm[b]))
        elif b in am and a in cm:
            abstract_side.append((c + am[b], cm[a]))
        elif a in am and b in am:
            abstract_side.append(tuple(sorted((c + am[a], c + am[b]))))
    return s, core, side_mask_of(c, s, abstract_side)


def boundary_degrees(c, s, side):
    answer = [0] * c
    for x, y in side_edges_of(c, s, side):
        if x >= c and y < c:
            answer[y] += 1
    return tuple(answer)


def canonical_pair(c, sl, sr, core, left, right):
    images = []
    for p in automorphisms(c, core):
        a = normalize_exclusive(c, sl, permute_side(c, sl, left, p, exclusive_perms(sl)[0]))
        b = normalize_exclusive(c, sr, permute_side(c, sr, right, p, exclusive_perms(sr)[0]))
        images.append(tuple(sorted((a, b))) if sl == sr else (a, b))
    return min(images)


def compatible(c, core, sl, left, sr, right):
    cd = tuple(sum(v in e for e in core_edges_of(c, core)) for v in range(c))
    ld = boundary_degrees(c, sl, left)
    rd = boundary_degrees(c, sr, right)
    return all(a + b + d <= 6 for a, b, d in zip(cd, ld, rd))


def local_graph(record):
    c, sl, sr = record["c"], record["s_left"], record["s_right"]
    core, left, right = record["core"], record["left"], record["right"]
    cstart = 2
    astart = cstart + c
    bstart = astart + sl
    answer = {edge(0, 1)}
    answer.update(edge(h, cstart + x) for h in (0, 1) for x in range(c))
    answer.update(edge(0, astart + a) for a in range(sl))
    answer.update(edge(1, bstart + b) for b in range(sr))
    answer.update(edge(cstart + a, cstart + b) for a, b in core_edges_of(c, core))

    def add_side(s, mask, start):
        for x, y in side_edges_of(c, s, mask):
            if x >= c and y >= c:
                answer.add(edge(start + x - c, start + y - c))
            else:
                answer.add(edge(start + x - c, cstart + y))

    add_side(sl, left, astart)
    add_side(sr, right, bstart)
    return 2 + c + sl + sr, frozenset(answer)


def main(args) -> int:
    root = Path(__file__).resolve().parent
    geng = root / "nauty" / "geng.exe"
    configs = defaultdict(lambda: defaultdict(set))  # (c,s) -> core -> sides
    link_counts = defaultdict(int)
    for n in range(5, 9):
        result = subprocess.run([str(geng), "-cq", str(n)], check=True, stdout=subprocess.PIPE, text=True)
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            order, graph = parse_graph6(line)
            if is_wke(order, graph):
                continue
            degrees = [sum(v in e for e in graph) for v in range(order)]
            for r, c in enumerate(degrees):
                if c < 4 or c > 7:
                    continue
                s, core, side = extract_configuration(order, graph, r, c)
                if s > 7 - c:
                    continue
                canonical, images = canonical_side_images(c, s, core, side)
                configs[c, s][canonical].update(images)
                link_counts[c, s] += 1

    records = []
    template_certificates = []
    for c in range(4, 8):
        sl = 7 - c
        for sr in range(sl + 1):
            common_cores = set(configs[c, sl]) & set(configs[c, sr])
            before = len(records)
            for core in sorted(common_cores):
                # The generalized template has one forced hub edge plus all
                # exclusive spokes from both endpoints.
                template = template_witness(core_edges_of(c, core), c, 1 + sl + sr)
                if template is not None:
                    chosen_r, chosen_q, packing = template
                    template_certificates.append(
                        {
                            "c": c,
                            "s_left": sl,
                            "s_right": sr,
                            "core": core,
                            "r": [list(e) for e in chosen_r],
                            "q": list(chosen_q),
                            "packing": [list(item) for item in packing],
                        }
                    )
                    continue
                lefts = sorted(configs[c, sl][core])
                rights = sorted(configs[c, sr][core])
                raw = {
                    canonical_pair(c, sl, sr, core, left, right)
                    for left in lefts
                    for right in rights
                    if compatible(c, core, sl, left, sr, right)
                }
                records.extend(
                    {"c": c, "s_left": sl, "s_right": sr, "core": core, "left": left, "right": right}
                    for left, right in sorted(raw)
                )
            print("PAIR_CLASS", "c", c, "s_left", sl, "s_right", sr, "orbits_requiring_solver", len(records) - before, flush=True)

    print("link_embedding_counts", {str(k): v for k, v in sorted(link_counts.items())})
    print("total_pair_orbits_requiring_solver", len(records))
    Path(args.output).write_text(json.dumps(records, indent=2), encoding="utf-8")
    print("pairs_written", args.output)
    if args.template_output:
        Path(args.template_output).write_text(json.dumps(template_certificates, indent=2), encoding="utf-8")
        print("template_certificates", len(template_certificates))
        print("template_certificates_written", args.template_output)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="work/tuza_delta8_mixed_pairs.json")
    parser.add_argument("--template-output")
    raise SystemExit(main(parser.parse_args()))
