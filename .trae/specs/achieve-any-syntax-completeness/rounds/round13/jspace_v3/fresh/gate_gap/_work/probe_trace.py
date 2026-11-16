#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only local probe tracer: run ONE source through the region pipeline
under coverage and report which line ranges were executed.

Usage:
    python -I -X utf8 probe_trace.py --src <file.py> [--show file:lo-hi ...]
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


def pyc_for(src, outdir):
    base = os.path.splitext(os.path.basename(src))[0] + ".pyc"
    out = os.path.join(outdir, base)
    py_compile.compile(src, cfile=out, doraise=True)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--pyc", default="")
    ap.add_argument("--show", action="append", default=[])
    ap.add_argument("--all", action="store_true", help="print every measured core file")
    args = ap.parse_args(argv)
    root = repo_root(HERE)
    os.chdir(root)
    sys.path.insert(0, root)

    src = os.path.abspath(args.src)
    pyc = args.pyc or pyc_for(src, tempfile.mkdtemp(prefix="pj_trace_"))
    with open(pyc, "rb") as fh:
        fh.read(16)
        code = marshal.load(fh)

    import coverage
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    from core.cfg.ast_converter import CFGASTConverter
    from core.cfg.code_generator import CFGCodeGenerator

    cov = coverage.Coverage(data_file=None, include=[os.path.join(root, "core", "*")])
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
    lines = {}
    for measured in cov.get_data().measured_files():
        fn = norm(measured)
        got = cov.get_data().lines(measured) or []
        lines[fn] = sorted(got)
    out = {"src": src, "pyc": pyc, "error": err,
           "measured": {k: len(v) for k, v in sorted(lines.items())}}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    for spec in args.show:
        rel, _, rng = spec.partition(":")
        lo, _, hi = rng.partition("-")
        lo, hi = int(lo), int(hi or lo)
        key = rel.replace("\\", "/")
        got = set(lines.get(key) or [])
        hit = [n for n in range(lo, hi + 1) if n in got]
        print("[show] %s %d-%d executed=%d %s" % (key, lo, hi, len(hit), hit))
    if args.all:
        for key in sorted(lines):
            print("[file] %s %d" % (key, len(lines[key])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
