#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remap the frozen 402/small34 baseline indexes to this checkout.

The frozen indexes store an absolute ``path`` from the machine that produced
them, plus a portable ``rel`` under ``site-packages``.  ``pyc_verify.py batch``
uses ``path`` first and aborts on a stale absolute path, so this script
rewrites only ``path`` (keeping ``rel``, ``size`` and ``function_count``) and
verifies that every current file exists with the frozen size.

Usage:
    python -X utf8 remap_baseline_indexes.py [--root <repo>] [--out <dir>]
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def load(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def main(argv=None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = here
    while not os.path.isdir(os.path.join(repo, "core", "cfg")):
        parent = os.path.dirname(repo)
        if parent == repo:
            raise SystemExit("cannot locate repo root from %s" % here)
        repo = parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=repo)
    parser.add_argument("--out", default=os.path.join(here, "shards"))
    args = parser.parse_args(argv)
    root = os.path.abspath(args.root)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    base = os.path.join(root, ".trae", "specs",
                        "region-reduction-v3-full-corpus-100pct-10rounds",
                        "baseline", "shards")
    report = {"root": root.replace("\\", "/"), "shards": [], "small34": None}
    total = missing = mismatch = 0
    for i in range(8):
        src = os.path.join(base, "shard%d.json" % i)
        rows = load(src)
        remapped = []
        miss = []
        bad = []
        for row in rows:
            rel = row["rel"]
            current = os.path.join(root, "site-packages", rel.replace("/", os.sep))
            if not os.path.isfile(current):
                miss.append(rel)
            elif row.get("size") and os.path.getsize(current) != row["size"]:
                bad.append({"rel": rel, "frozen": row["size"],
                            "current": os.path.getsize(current)})
            item = dict(row)
            item["path"] = current.replace("\\", "/")
            remapped.append(item)
        total += len(rows)
        missing += len(miss)
        mismatch += len(bad)
        dst = os.path.join(out, "shard%d.json" % i)
        with open(dst, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(remapped, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        report["shards"].append({"shard": i, "entries": len(rows),
                                 "missing": miss, "size_mismatch": bad,
                                 "out": dst.replace("\\", "/")})
        print("[remap] shard%d entries=%d missing=%d mismatch=%d"
              % (i, len(rows), len(miss), len(bad)))

    small_src = os.path.join(base, "..", "small34_index.json")
    rows = load(small_src)
    remapped = []
    miss = []
    bad = []
    for row in rows:
        rel = row["rel"]
        current = os.path.join(root, "site-packages", rel.replace("/", os.sep))
        if not os.path.isfile(current):
            miss.append(rel)
        elif row.get("size") and os.path.getsize(current) != row["size"]:
            bad.append({"rel": rel, "frozen": row["size"],
                        "current": os.path.getsize(current)})
        item = dict(row)
        item["path"] = current.replace("\\", "/")
        remapped.append(item)
    total += len(rows)
    missing += len(miss)
    mismatch += len(bad)
    dst = os.path.join(out, "small34.json")
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(remapped, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    report["small34"] = {"entries": len(rows), "missing": miss,
                         "size_mismatch": bad, "out": dst.replace("\\", "/")}
    report["total_entries"] = total
    report["missing_total"] = missing
    report["size_mismatch_total"] = mismatch
    with open(os.path.join(out, "remap_report.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("[remap] total=%d missing=%d mismatch=%d" % (total, missing, mismatch))
    return 0 if missing == 0 and mismatch == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
