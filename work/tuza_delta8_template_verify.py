#!/usr/bin/env python3
"""Optimizer-free verifier for generalized two-hub template certificates."""

from __future__ import annotations

import argparse
from itertools import combinations
import json
from pathlib import Path


def edge(a, b):
    assert a != b
    return (a, b) if a < b else (b, a)


def core_edges(c, mask):
    pairs = tuple(combinations(range(c), 2))
    assert 0 <= mask < (1 << len(pairs))
    return frozenset(e for i, e in enumerate(pairs) if (mask >> i) & 1)


def verify(item):
    c = item["c"]
    sl = item["s_left"]
    sr = item["s_right"]
    assert sl == 7 - c and 0 <= sr <= sl
    core = core_edges(c, item["core"])
    r = frozenset(edge(*e) for e in item["r"])
    q = frozenset(item["q"])
    assert len(r) == len(item["r"]) and r <= core
    assert len(q) == len(item["q"]) and all(0 <= x < c for x in q)
    assert all(e in r or e[0] in q or e[1] in q for e in core)

    # Realize the abstract packing on vertices u=c, v=c+1.
    u, v = c, c + 1
    packing = []
    for kind, payload in item["packing"]:
        if kind == "uv":
            assert 0 <= payload < c
            triangle = (u, v, payload)
        else:
            assert kind in ("u", "v")
            rim = edge(*payload)
            assert rim in r
            triangle = ((u if kind == "u" else v), rim[0], rim[1])
        packing.append(triangle)

    used = set()
    for triangle in packing:
        te = frozenset(edge(a, b) for a, b in combinations(triangle, 2))
        assert not (te & used)
        used.update(te)

    forced = 1 + sl + sr
    assert forced + len(r) + 2 * len(q) <= 2 * len(packing)


def main(args):
    catalogue = json.loads(Path(args.catalogue).read_text(encoding="utf-8"))
    keys = set()
    for item in catalogue:
        key = (item["c"], item["s_left"], item["s_right"], item["core"])
        assert key not in keys
        keys.add(key)
        verify(item)
    print("verified_template_certificates", len(catalogue))
    print("ALL TEMPLATE CERTIFICATES VERIFIED WITHOUT AN OPTIMIZER")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("catalogue")
    raise SystemExit(main(parser.parse_args()))
