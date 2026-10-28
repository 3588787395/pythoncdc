#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classify the 152 never-hit G4 rules without inventing coverage.

Inputs (frozen, read-only):
  rounds/round9/rule_universe.json
  rounds/round9/rule_traces.json
  rounds/round9/g4_never_hit_rules.json
  rounds/round9/rule_coverage.json

For every never-hit rule this audit finds the innermost enclosing function
(or class body / module body) and asks two independent questions:

  1. Did any *other* rule anchored in the same function execute in the frozen
     trace?  If yes, the function ran and the never-hit anchor is an
     unexercised branch.  If no, the function was never observed running.
  2. Is the enclosing function referenced anywhere in the product sources
     (``core/cfg``, ``core``, ``parsers``, ``pycdc.py``)?  A zero-reference
     function is a dead-code candidate, not proof of dead code.

The output is a classification, not a proof and not a coverage claim.  It is
used to decide whether G4's ``empty_cov`` can be reduced by more J entries or
is structurally blocked by dead/unreachable code.
"""
from __future__ import annotations

import argparse
import ast
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND9 = os.path.join(HERE, "..", "..", "..", "..", "..", "..",
                      "attack-completeness-claims", "rounds", "round9")


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


class ScopeFinder(ast.NodeVisitor):
    def __init__(self):
        self.stack = []
        self.spans = []

    def _enter(self, node, kind, name):
        self.stack.append((kind, name, node.lineno,
                           getattr(node, "end_lineno", node.lineno)))

    def _exit(self):
        kind, name, start, end = self.stack.pop()
        self.spans.append({"kind": kind, "name": name, "start": start,
                           "end": end,
                           "qualified": ".".join(x[1] for x in self.stack + [(kind, name, start, end)])})

    def visit_FunctionDef(self, node):
        self._enter(node, "function", node.name)
        self.generic_visit(node)
        self._exit()

    def visit_AsyncFunctionDef(self, node):
        self._enter(node, "function", node.name)
        self.generic_visit(node)
        self._exit()

    def visit_ClassDef(self, node):
        self._enter(node, "class", node.name)
        self.generic_visit(node)
        self._exit()


def enclosing(spans, line):
    best = None
    for span in spans:
        if span["start"] <= line <= span["end"]:
            if best is None or (span["end"] - span["start"]) < (best["end"] - best["start"]):
                best = span
    return best


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="")
    parser.add_argument("--round9", default=ROUND9)
    parser.add_argument("--universe", default="")
    parser.add_argument("--traces", default="")
    parser.add_argument("--never", default="")
    parser.add_argument("--coverage", default="")
    parser.add_argument("--out", default=os.path.join(HERE, "G4_REACHABILITY.json"))
    args = parser.parse_args(argv)
    root = repo_root(args.root or HERE)
    r9 = os.path.abspath(args.round9)
    universe_path = os.path.abspath(args.universe) if args.universe else os.path.join(r9, "rule_universe.json")
    traces_path = os.path.abspath(args.traces) if args.traces else os.path.join(r9, "rule_traces.json")
    never_path = os.path.abspath(args.never) if args.never else os.path.join(r9, "g4_never_hit_rules.json")
    coverage_path = os.path.abspath(args.coverage) if args.coverage else os.path.join(r9, "rule_coverage.json")

    universe = load(universe_path)
    traces = load(traces_path)
    coverage = load(coverage_path)
    rules = {r["rule_id"]: r for r in universe["rules"]}
    if args.never:
        never = load(never_path)
        never_ids = {r["rule_id"] for r in never}
    else:
        # Derive from the check output: coverage maps rule_id -> entry ids.
        never_ids = {rid for rid, ids in (coverage.get("coverage") or {}).items() if not ids}
        if not never_ids:
            never = load(never_path)
            never_ids = {r["rule_id"] for r in never}

    hit_by_rule = collections.defaultdict(set)
    for rec in traces.get("records") or []:
        for rid in rec.get("rule_ids") or []:
            hit_by_rule[rid].add(rec["entry_id"])

    files = sorted({r["file"] for r in universe["rules"]})
    spans_by_file = {}
    names_by_file = {}
    for rel in files:
        path = os.path.join(root, rel)
        with open(path, encoding="utf-8-sig") as fh:
            tree = ast.parse(fh.read(), rel)
        finder = ScopeFinder()
        finder.visit(tree)
        spans_by_file[rel] = finder.spans
        names = collections.Counter()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names[node.id] += 1
            elif isinstance(node, ast.Attribute):
                names[node.attr] += 1
        names_by_file[rel] = names

    # Cross-file reference counts (names are not resolved; this is a candidate
    # signal only).  Exclude the definition's own name node by subtracting one
    # occurrence per definition.
    product_files = []
    for base in ("core/cfg", "core", "parsers"):
        for dirpath, _dirnames, filenames in os.walk(os.path.join(root, base)):
            for name in filenames:
                if name.endswith(".py"):
                    product_files.append(os.path.join(dirpath, name))
    product_files.append(os.path.join(root, "pycdc.py"))
    product_files = sorted(set(product_files))
    refs = collections.Counter()
    parse_errors = []
    for path in product_files:
        try:
            with open(path, encoding="utf-8-sig") as fh:
                tree = ast.parse(fh.read(), path)
        except Exception as exc:
            parse_errors.append({"file": path.replace("\\", "/"),
                                 "error": "%s: %s" % (type(exc).__name__, exc)})
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                refs[node.id] += 1
            elif isinstance(node, ast.Attribute):
                refs[node.attr] += 1

    # Import graph (direct, top-level imports only) to label files that the
    # region path never imports.
    imported_by_region = set()
    for path in product_files:
        rel = os.path.relpath(path, root).replace("\\", "/")
        if rel not in ("pycdc.py", "core/cfg/__init__.py",
                       "core/cfg/region_ast_generator.py",
                       "core/cfg/region_analyzer.py",
                       "core/cfg/code_generator.py",
                       "core/cfg/ast_converter.py",
                       "core/cfg/cfg_builder.py",
                       "core/cfg/basic_block.py",
                       "core/cfg/structured_analyzer.py"):
            continue
        try:
            with open(path, encoding="utf-8-sig") as fh:
                tree = ast.parse(fh.read(), path)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_by_region.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_by_region.add(alias.name)

    # Map every rule to its innermost enclosing scope once, so a nested def
    # does not inherit the outer function's coverage.
    scope_of_rule = {}
    rules_by_scope = collections.defaultdict(list)
    for rid, rule in rules.items():
        span = enclosing(spans_by_file[rule["file"]], int(rule["line"]))
        key = (rule["file"],
               span["qualified"] if span else "<module>",
               span["start"] if span else 1,
               span["end"] if span else 10 ** 9)
        scope_of_rule[rid] = (span, key)
        rules_by_scope[key].append(rid)

    rows = []
    for rid in sorted(never_ids):
        rule = rules[rid]
        rel = rule["file"]
        line = int(rule["line"])
        span, key = scope_of_rule[rid]
        fn = span["qualified"] if span else "<module>"
        fn_start = span["start"] if span else 1
        fn_end = span["end"] if span else 10 ** 9
        fn_rules = rules_by_scope[key]
        fn_hit = [x for x in fn_rules if hit_by_rule.get(x)]
        name = span["name"] if span else "<module>"
        own_refs = refs.get(name, 0)
        rows.append({
            "rule_id": rid,
            "anchor": rule["anchor"],
            "file": rel,
            "line": line,
            "pattern": rule.get("pattern"),
            "scope": fn,
            "scope_kind": span["kind"] if span else "module",
            "scope_start": fn_start,
            "scope_end": fn_end,
            "rules_in_scope": len(fn_rules),
            "hit_rules_in_scope": len(fn_hit),
            "scope_observed": bool(fn_hit),
            "name": name,
            "name_refs_all_sources": own_refs,
            "file_imported_by_region_path": any(
                rel.endswith(mod.replace(".", "/") + ".py")
                for mod in imported_by_region),
            "classification": (
                "scope_observed_branch_unhit" if fn_hit else
                "scope_never_observed_zero_refs" if own_refs == 0 else
                "scope_never_observed_has_refs"),
        })

    summary = collections.Counter(row["classification"] for row in rows)
    by_file = collections.defaultdict(collections.Counter)
    for row in rows:
        by_file[row["file"]][row["classification"]] += 1
    result = {
        "tool": "g4_reachability_audit",
        "version": "1.0.0",
        "root": root.replace("\\", "/"),
        "inputs": {
            "universe": universe_path.replace("\\", "/"),
            "traces": traces_path.replace("\\", "/"),
            "never_hit": never_path.replace("\\", "/") if args.never else None,
            "coverage": coverage_path.replace("\\", "/"),
        },
        "readings": {
            "total_rules": coverage.get("total_rules"),
            "proved": coverage.get("proved"),
            "open": coverage.get("open"),
            "empty_cov": coverage.get("empty_cov"),
            "g4": coverage.get("g4"),
            "reason": coverage.get("reason"),
            "traced_entries": (traces.get("summary") or {}).get("traced_entries"),
            "never_hit_rules": len(rows),
        },
        "summary": dict(sorted(summary.items())),
        "by_file": {k: dict(sorted(v.items())) for k, v in sorted(by_file.items())},
        "parse_errors": parse_errors,
        "rules": rows,
        "note": ("Classification is a candidate signal from frozen traces + "
                 "name references; it is not a dead-code proof and does not "
                 "change G4.  scope_observed_branch_unhit means the enclosing "
                 "function ran but the anchor line did not."),
    }
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("[g4] total=%s proved=%s open=%s empty_cov=%s g4=%s"
          % (result["readings"]["total_rules"], result["readings"]["proved"],
             result["readings"]["open"], result["readings"]["empty_cov"],
             result["readings"]["g4"]))
    for key, value in sorted(summary.items()):
        print("[g4] %-40s %d" % (key, value))
    print("[g4] wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
