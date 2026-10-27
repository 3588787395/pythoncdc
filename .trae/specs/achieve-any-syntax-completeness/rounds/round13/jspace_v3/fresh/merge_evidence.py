#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge fresh J v3 semantic_runner shards (and an optional repair shard).

Run from the repository root:

    python -X utf8 .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/merge_evidence.py \
        --out .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/semantic_v3_merged.json \
        --shard .../semantic_shard0.json --shard .../semantic_shard1.json --shard .../semantic_shard2.json

Add `--repair .../semantic_repair.json` to replace the repaired entries by ID.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import sys

TOOL_VERSION = "1.0.0"


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--shard", action="append", default=[])
    parser.add_argument("--repair", default="")
    parser.add_argument("--space", default="")
    args = parser.parse_args(argv)

    records = {}
    order = []
    sources = []
    for path in args.shard:
        payload = load(path)
        sources.append(os.path.relpath(os.path.abspath(path), os.getcwd()).replace("\\", "/"))
        for record in payload.get("records", []):
            eid = record.get("entry_id")
            if not isinstance(eid, str) or not eid:
                continue
            if eid in records:
                raise SystemExit("duplicate entry_id across shards: %s" % eid)
            records[eid] = record
            order.append(eid)

    replaced = []
    if args.repair:
        payload = load(args.repair)
        sources.append(os.path.relpath(os.path.abspath(args.repair), os.getcwd()).replace("\\", "/"))
        for record in payload.get("records", []):
            eid = record.get("entry_id")
            if not isinstance(eid, str) or not eid:
                continue
            if eid in records:
                replaced.append(eid)
            else:
                order.append(eid)
            records[eid] = record

    merged = [records[eid] for eid in order]
    verdicts = collections.Counter(record.get("c4", {}).get("verdict", "NO_C4") for record in merged)
    statuses = collections.Counter(record.get("status", "-") for record in merged)
    payload = {
        "tool": "merge_fresh_evidence",
        "version": TOOL_VERSION,
        "space": args.space,
        "sources": sources,
        "records": merged,
        "summary": {
            "total": len(merged),
            "verdicts": dict(sorted(verdicts.items())),
            "statuses": dict(sorted(statuses.items())),
            "replaced_by_repair": len(replaced),
        },
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("[merge] records=%d verdicts=%s statuses=%s replaced=%d"
          % (len(merged), dict(verdicts), dict(statuses), len(replaced)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
