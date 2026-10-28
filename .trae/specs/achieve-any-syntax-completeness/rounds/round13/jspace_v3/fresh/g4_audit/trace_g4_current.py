#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate G4 rule traces against the current core/cfg sources.

This is the current-tree counterpart of ``_r7_g4_trace.py``.  It uses the
current rule universe (not the stale round9 one), the current region pipeline,
and the same 131 unique pycs referenced by the frozen J space.  Output is a
new trace file; the round9 trace is never overwritten.

Usage:
    python -X utf8 trace_g4_current.py \
        --universe <current universe> --jspace <judgment_space.json> \
        --out <current traces>
"""
from __future__ import annotations

import argparse
import json
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def repo_root(start):
    cur = os.path.abspath(start)
    while not os.path.isdir(os.path.join(cur, "core", "cfg")):
        parent = os.path.dirname(cur)
        if parent == cur:
            raise SystemExit("cannot locate repo root")
        cur = parent
    return cur


def load(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def norm(p):
    p = p.replace("\\", "/")
    i = p.find("core/")
    return p[i:] if i >= 0 else p


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="")
    parser.add_argument("--universe", required=True)
    parser.add_argument("--jspace", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    root = repo_root(args.root or HERE)
    os.chdir(root)
    sys.path.insert(0, root)

    universe = load(args.universe)
    rules = universe["rules"]
    line_rules = {}
    for rule in rules:
        line_rules.setdefault((rule["file"], int(rule["line"])), []).append(rule["rule_id"])
        for anchor in rule.get("anchors") or []:
            rel, _, line = anchor.rpartition(":")
            try:
                line_rules.setdefault((rel, int(line)), []).append(rule["rule_id"])
            except ValueError:
                pass

    import coverage
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    from core.cfg.ast_converter import CFGASTConverter
    from core.cfg.code_generator import CFGCodeGenerator

    space = load(args.jspace)
    pyc_entries = {}
    for entry in space.get("entries") or []:
        pyc = entry.get("pyc")
        if pyc and os.path.isfile(pyc):
            pyc_entries.setdefault(pyc.replace("\\", "/"), []).append(entry["id"])

    cov = coverage.Coverage(data_file=None)
    result = {}
    failed = {}
    for i, (pyc, eids) in enumerate(sorted(pyc_entries.items())):
        try:
            with open(pyc, "rb") as fh:
                fh.read(16)
                code = marshal.load(fh)
            cov.erase()
            cov.start()
            try:
                cfg = build_cfg(code)
                gen = RegionASTGenerator(
                    cfg, top_level_code=code if code.co_name == "<module>" else None)
                ast_dict = gen.generate()
                py_ast = CFGASTConverter().convert(ast_dict)
                CFGCodeGenerator().generate(py_ast)
            finally:
                cov.stop()
            data = cov.get_data()
            hit_rules = set()
            for measured in data.measured_files():
                fn = norm(measured)
                for line in (data.lines(measured) or []):
                    for rid in line_rules.get((fn, line), []):
                        hit_rules.add(rid)
            for eid in eids:
                result[eid] = sorted(hit_rules)
        except BaseException as exc:
            for eid in eids:
                failed[eid] = "%s: %s" % (type(exc).__name__, exc)
        if (i + 1) % 20 == 0:
            print("[trace] %d/%d" % (i + 1, len(pyc_entries)), flush=True)

    records = [{"entry_id": eid, "rule_ids": rids}
               for eid, rids in sorted(result.items())]
    payload = {
        "tool": "g4-current-line-coverage-trace",
        "version": "1.0.0",
        "note": ("Current-tree replay of Task 6.4: per-entry executed rule anchor "
                 "lines (coverage.py C tracer, in-process region pipeline)."),
        "universe": os.path.abspath(args.universe).replace("\\", "/"),
        "jspace": os.path.abspath(args.jspace).replace("\\", "/"),
        "records": records,
        "summary": {"traced_entries": len(result),
                    "failed_entries": len(failed),
                    "failures": dict(list(failed.items())[:10])},
    }
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False)
        fh.write("\n")
    all_hit = set()
    for rids in result.values():
        all_hit.update(rids)
    never = [r for r in rules if r["rule_id"] not in all_hit]
    print("[trace] entries=%d failed=%d rules_hit=%d/%d never_hit=%d"
          % (len(result), len(failed), len(all_hit), len(rules), len(never)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
