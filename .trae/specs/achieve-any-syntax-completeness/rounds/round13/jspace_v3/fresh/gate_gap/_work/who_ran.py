#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report, per file, which functions executed (by line ranges) for one source."""
from __future__ import annotations

import argparse
import ast
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


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--pyc", default="")
    ap.add_argument("--files", action="append", default=[])
    args = ap.parse_args(argv)
    root = repo_root(HERE)
    os.chdir(root)
    sys.path.insert(0, root)
    files = args.files or ["core/cfg/ast_generator_v2.py", "core/cfg/code_generator.py",
                           "core/cfg/structured_analyzer.py",
                           "core/cfg/objective_patch_detector.py",
                           "core/cfg/patch_detector.py",
                           "core/cfg/region_ast_generator.py"]

    pyc = args.pyc or py_compile.compile(
        os.path.abspath(args.src),
        cfile=os.path.join(tempfile.mkdtemp(prefix="pj_"),
                           os.path.basename(args.src) + "c"), doraise=True)
    with open(pyc, "rb") as fh:
        fh.read(16)
        code = marshal.load(fh)

    sys.path.insert(0, root)
    import coverage
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    from core.cfg.ast_converter import CFGASTConverter
    from core.cfg.code_generator import CFGCodeGenerator

    cov = coverage.Coverage(data_file=None)
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
    executed = {}
    for measured in cov.get_data().measured_files():
        executed[norm(measured)] = set(cov.get_data().lines(measured) or [])

    # build def table per file
    print(json.dumps({"src": args.src, "error": err}, ensure_ascii=False))
    for rel in files:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        tree = ast.parse(open(path, encoding="utf-8-sig").read())
        table = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                table.append((node.lineno, node.end_lineno, node.name))
        got = executed.get(rel, set())
        rows = []
        for lo, hi, name in table:
            n = sum(1 for x in got if lo <= x <= hi)
            if n:
                rows.append((lo, hi, name, n, hi - lo + 1))
        print("== %s executed_lines=%d" % (rel, len(got)))
        for lo, hi, name, n, total in sorted(rows):
            print("   %-45s %5d-%-5d %d/%d" % (name, lo, hi, n, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
