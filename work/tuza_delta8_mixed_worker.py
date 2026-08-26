#!/usr/bin/env python3
"""Sharded exact reducer for asymmetric delta-8 local pairs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tuza_delta8_mixed_pairs import local_graph
from tuza_delta8_pair_probe import reduction_witness


def main(args) -> int:
    records = json.loads(Path(args.pairs).read_text(encoding="utf-8"))
    indexed = list(enumerate(records))
    if args.mixed_only:
        indexed = [(i, r) for i, r in indexed if r["s_right"] < r["s_left"]]
    selected = [(i, r) for position, (i, r) in enumerate(indexed) if position % args.shards == args.shard]
    obstructions = []
    witnesses = []
    for number, (index, record) in enumerate(selected, 1):
        vertices, graph = local_graph(record)
        witness = reduction_witness(vertices, graph)
        if witness is None:
            obstructions.append({"index": index, **record})
            print("OBSTRUCTION", index, record, flush=True)
        elif args.save_witnesses:
            packing, cover = witness
            witnesses.append(
                {
                    "index": index,
                    "packing": [list(t) for t in packing],
                    "cover": [list(e) for e in sorted(cover)],
                }
            )
        if number % 100 == 0:
            print("progress", number, "/", len(selected), "obstructions", len(obstructions), flush=True)
    Path(args.output).write_text(
        json.dumps(
            {
                "shard": args.shard,
                "shards": args.shards,
                "checked": len(selected),
                "obstructions": obstructions,
                "witnesses": witnesses if args.save_witnesses else None,
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    print("DONE", args.shard, "checked", len(selected), "obstructions", len(obstructions))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", default="work/tuza_delta8_mixed_pairs.json")
    parser.add_argument("--shards", type=int, required=True)
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mixed-only", action="store_true")
    parser.add_argument("--save-witnesses", action="store_true")
    raise SystemExit(main(parser.parse_args()))
