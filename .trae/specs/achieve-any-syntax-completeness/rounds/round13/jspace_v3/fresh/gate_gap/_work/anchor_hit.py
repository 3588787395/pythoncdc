#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only: run ONE source through the region pipeline and report which of the
G4 empty-coverage rule anchors (any cluster) get executed.

Usage:
    python -I -X utf8 anchor_hit.py --src <src.py> [--pyc <f.pyc>] [--cluster N]
                                   [--ranges] [--json <out>]
"""
from __future__ import annotations

import argparse
import json
import marshal
import os
import py_compile
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)


def repo_root(start):
    cur = os.path.abspath(start)
    while not os.path.isdir(os.path.join(cur, "core", "cfg")):
        parent = os.path.dirname(cur)
        if parent == cur:
            raise SystemExit("cannot locate repo root")
        cur = parent
    return cur


def norm(p):
    p = p.replace("\\", "/")
    i = p.find("core/")
    return p[i:] if i >= 0 else p


def load(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def target_rules(root, clusters):
    gap = os.path.join(root, ".trae", "specs", "achieve-any-syntax-completeness",
                       "rounds", "round13", "jspace_v3", "fresh", "gate_gap")
    aud = os.path.join(root, ".trae", "specs", "achieve-any-syntax-completeness",
                       "rounds", "round13", "jspace_v3", "fresh", "g4_audit")
    empty = load(os.path.join(gap, "g4_empty_cov.json"))
    universe = load(os.path.join(aud, "rule_universe_current.json"))
    um = {r["rule_id"]: r for r in universe["rules"]}
    want = {}
    for i, c in enumerate(empty["clusters"], 1):
        if clusters and i not in clusters:
            continue
        for rid in c["empty_rule_ids"]:
            want[rid] = i
    lines = {}
    for rid, cid in want.items():
        rule = um[rid]
        for a in (rule.get("anchors") or [rule["anchor"]]):
            rel, _, ln = a.rpartition(":")
            try:
                ln = int(ln)
            except ValueError:
                continue
            lines.setdefault((rel, ln), []).append((rid, cid))
    files = sorted({f for f, _ in lines})
    return want, lines, files


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--pyc", default="")
    ap.add_argument("--cluster", action="append", type=int, default=[])
    ap.add_argument("--json", default="")
    args = ap.parse_args(argv)
    root = repo_root(HERE)
    os.chdir(root)
    sys.path.insert(0, root)

    want, anchor_lines, files = target_rules(root, set(args.cluster) if args.cluster else None)

    src = os.path.abspath(args.src)
    pyc = args.pyc or py_compile.compile(
        src, cfile=os.path.join(tempfile.mkdtemp(prefix="pj_"), os.path.basename(src) + "c"),
        doraise=True)
    with open(pyc, "rb") as fh:
        fh.read(16)
        code = marshal.load(fh)

    import coverage
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    from core.cfg.ast_converter import CFGASTConverter
    from core.cfg.code_generator import CFGCodeGenerator

    cov = coverage.Coverage(data_file=None, include=[os.path.join(root, f) for f in files])
    cov.erase()
    cov.start()
    err = None
    try:
        cfg = build_cfg(code)
        gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == "<module>" else None)
        ast_dict = gen.generate()
        py_ast = CFGASTConverter().convert(ast_dict)
        CFGCodeGenerator().generate(py_ast)
    except BaseException as exc:  # noqa: BLE001
        err = "%s: %s" % (type(exc).__name__, exc)
    finally:
        cov.stop()

    got = {}
    for measured in cov.get_data().measured_files():
        fn = norm(measured)
        for ln in (cov.get_data().lines(measured) or []):
            got.setdefault(fn, set()).add(ln)
    hits = {}
    for (rel, ln), rids in anchor_lines.items():
        if ln in got.get(rel, ()):  # noqa: E501
            for rid, cid in rids:
                hits.setdefault(rid, cid)
    print(json.dumps({"src": src, "error": err,
                      "target_rules": len(want), "hit": len(hits)}, ensure_ascii=False))
    by_cluster = {}
    for rid, cid in hits.items():
        by_cluster.setdefault(cid, []).append(rid)
    for cid in sorted({want[r] for r in want}):
        print("  cluster %d: hit %d/%d"
              % (cid, len(by_cluster.get(cid, [])),
                 sum(1 for r, c in want.items() if c == cid)))
    for (rel, ln) in sorted(anchor_lines):
        mark = "HIT " if ln in got.get(rel, set()) else "    "
        if mark.strip():
            print("  %s%s:%d -> %s" % (mark, rel, ln,
                                       [r for r, _ in anchor_lines[(rel, ln)]]))
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"hit": sorted(hits)}, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
