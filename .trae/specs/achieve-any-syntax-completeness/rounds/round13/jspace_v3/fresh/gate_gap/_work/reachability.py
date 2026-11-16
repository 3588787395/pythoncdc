#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static reachability evidence for the five gate_gap clusters (read-only).

For every entry point that the five clusters depend on, list each reference in
core/ together with its enclosing function, and mark whether that caller is on
the fixed trace pipeline:

    build_cfg -> RegionASTGenerator.generate -> CFGASTConverter.convert
              -> CFGCodeGenerator.generate

Output: fresh/gate_gap/g4_probe_reachability.json
"""
from __future__ import annotations

import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)

ENTRY_POINTS = [
    ("_generate_dict_node", "cluster 1 (CoreGenerator._generate_dict_node)"),
    ("_decompile_nested_code", "bridge: code_generator -> generate_ast_v2"),
    ("generate_ast_v2", "bridge: legacy v2 generator entry"),
    ("ASTGeneratorV2", "cluster 2/3 owner (legacy class)"),
    ("_generate_if_ast", "cluster 2"),
    ("extract_elif_chain", "cluster 3"),
    ("StructuredAnalyzer", "cluster 4 owner"),
    ("_identify_with_structures", "cluster 4"),
    ("ObjectivePatchDetector", "cluster 5 owner"),
    ("_extract_test_pattern", "cluster 5"),
    ("patch_detector", "cluster 5 sibling anchors"),
]

# files that the trace pipeline itself imports at start-up (measured only from
# the moment coverage starts, i.e. function bodies, not module bodies)
PIPELINE = ["core/cfg/cfg_builder.py", "core/cfg/region_ast_generator.py",
            "core/cfg/ast_converter.py", "core/cfg/code_generator.py",
            "core/cfg/region_analyzer.py", "core/cfg/basic_block.py",
            "core/cfg/comprehension_generator.py", "core/cfg/pattern_parser.py",
            "core/cfg/peephole_patterns.py", "core/cfg/opcode_feature_detector.py",
            "core/cfg/dominator_analyzer.py"]


def enclosing(tree, lineno):
    best = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            end = getattr(node, "end_lineno", lineno)
            if node.lineno <= lineno <= end:
                if best is None or node.lineno >= best[0]:
                    best = (node.lineno, node.name)
    return best


def main():
    root = GAP
    while not os.path.isdir(os.path.join(root, "core", "cfg")):
        nxt = os.path.dirname(root)
        if nxt == root:
            raise SystemExit("repo root not found")
        root = nxt
    records = {name: [] for name, _ in ENTRY_POINTS}
    for name, _ in ENTRY_POINTS:
        for base, dirs, files in os.walk(os.path.join(root, "core")):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in sorted(files):
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(base, fn)
                rel = os.path.relpath(path, root).replace("\\", "/")
                try:
                    text = open(path, encoding="utf-8-sig").read()
                    tree = ast.parse(text)
                except (OSError, SyntaxError):
                    continue
                for i, line in enumerate(text.splitlines(), 1):
                    if name not in line:
                        continue
                    owner = enclosing(tree, i)
                    records[name].append({
                        "file": rel,
                        "line": i,
                        "owner": owner[1] if owner else "<module>",
                        "owner_line": owner[0] if owner else 0,
                        "text": line.strip()[:120],
                        "is_import": line.strip().startswith(("import ", "from ")),
                        "on_pipeline_file": rel in PIPELINE,
                    })
    payload = {
        "tool": "g4_probe_reachability",
        "version": "1.0.0",
        "note": ("Static caller map for the five gate_gap cluster entry points. "
                 "The trace pipeline is fixed by fresh/g4_audit/trace_g4_current.py: "
                 "build_cfg -> RegionASTGenerator.generate -> CFGASTConverter.convert "
                 "-> CFGCodeGenerator.generate."),
        "pipeline_files": PIPELINE,
        "entry_points": [{"name": n, "clusters": why,
                          "references": records[n]} for n, why in ENTRY_POINTS],
    }
    out = os.path.join(GAP, "g4_probe_reachability.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    for n, _ in ENTRY_POINTS:
        refs = records[n]
        files = sorted({r["file"] for r in refs})
        print("%-26s refs=%3d files=%s" % (n, len(refs), files))
    print("[reachability]", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
