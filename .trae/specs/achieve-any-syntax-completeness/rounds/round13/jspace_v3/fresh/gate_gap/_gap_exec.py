#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collect executed *lines* (not just rule hits) for the region pipeline.

Read-only instrumentation: replays exactly the same in-process region pipeline
as ``trace_g4_current.py`` over the pycs referenced by the J space, but records
the raw executed line set of every core/cfg file instead of rule ids.

Output: JSON {file: [lines]} + summary, written to --out.

    python -I -X utf8 _gap_exec.py --jspace <judgment_space.json> --out <json>
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
    parser.add_argument("--jspace", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    root = repo_root(args.root or HERE)
    os.chdir(root)
    sys.path.insert(0, root)

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
    union = {}
    per_pyc = {}
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
            seen = {}
            for measured in data.measured_files():
                fn = norm(measured)
                lines = sorted(data.lines(measured) or [])
                if not lines:
                    continue
                seen[fn] = lines
                bucket = union.setdefault(fn, set())
                bucket.update(lines)
            per_pyc[pyc] = {"entries": eids, "files": seen}
        except BaseException as exc:
            failed[pyc] = "%s: %s" % (type(exc).__name__, exc)
        if (i + 1) % 20 == 0:
            print("[exec] %d/%d" % (i + 1, len(pyc_entries)), flush=True)

    payload = {
        "tool": "g4-executed-lines",
        "version": "1.0.0",
        "note": ("Raw executed line numbers per core/cfg file for the current region "
                 "pipeline over the J-space pycs (union across all entries)."),
        "jspace": os.path.abspath(args.jspace).replace("\\", "/"),
        "union": {k: sorted(v) for k, v in sorted(union.items())},
        "per_pyc": per_pyc,
        "summary": {
            "pycs": len(pyc_entries),
            "traced": len(per_pyc),
            "failed": len(failed),
            "failures": dict(list(failed.items())[:10]),
            "files_with_lines": len(union),
            "total_lines": sum(len(v) for v in union.values()),
        },
    }
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False)
        fh.write("\n")
    cfg_files = sorted(f for f in union if f.startswith("core/cfg/"))
    print("[exec] traced=%d failed=%d files=%d total_lines=%d cfg_files=%d"
          % (len(per_pyc), len(failed), len(union),
             sum(len(v) for v in union.values()), len(cfg_files)))
    for f in cfg_files:
        print("[exec]   %-42s %6d lines" % (f, len(union[f])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
