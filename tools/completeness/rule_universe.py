#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent rule-universe enumerator for G4 (Task 9.4).

The universe is derived statically from core/cfg/** dispatch branches:

  * isinstance(x, ast.X) branches
  * opname/opcode/name == "X" branches
  * node.__class__.__name__ == "X" branches
  * region-type tuple/list assignments

It never reads rule_manifest.json.  Manifest mapping is a separate step.

CLI:
    python -X utf8 tools/completeness/rule_universe.py --code core/cfg \
        --json .trae/specs/attack-completeness-claims/rounds/round9/rule_universe.json
"""

from __future__ import annotations

import argparse
import ast
import collections
import glob
import hashlib
import json
import os
import sys

TOOL_VERSION = "1.0.0"
OP_NAMES = {"opname", "opcode", "name", "kind", "node_type", "node_name"}


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _str_constant(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _op_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _ast_attr(node):
    if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
            and node.value.id == "ast"):
        return node.attr
    return None


def _isinstance_types(test):
    if not isinstance(test, ast.Call) or len(test.args) < 2:
        return []
    func = test.func
    if not (isinstance(func, ast.Name) and func.id == "isinstance"):
        return []
    arg = test.args[1]
    nodes = arg.elts if isinstance(arg, ast.Tuple) else [arg]
    out = []
    for item in nodes:
        name = _ast_attr(item)
        if name:
            out.append(name)
    return out


def _class_name_tests(test):
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return []
    left, op, right = test.left, test.ops[0], test.comparators[0]
    if not isinstance(op, ast.Eq):
        return []
    needle = _str_constant(right)
    if not needle:
        return []
    text = ast.dump(left)
    if "__class__" in text and "__name__" in text:
        return [needle]
    if isinstance(left, ast.Call) and isinstance(left.func, ast.Name) and left.func.id == "type":
        if left.args and ast.dump(left.args[0]).find("__class__") >= 0:
            return [needle]
    return []


def _opcode_tests(test):
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return []
    left, op, right = test.left, test.ops[0], test.comparators[0]
    if _op_name(left) not in OP_NAMES:
        return []
    if isinstance(op, ast.Eq) and _str_constant(right):
        return [_str_constant(right)]
    if isinstance(op, ast.In):
        container = right
        if isinstance(container, (ast.Tuple, ast.List, ast.Set)):
            return [v for v in (_str_constant(x) for x in container.elts) if v]
        if isinstance(container, (ast.Name, ast.Attribute)):
            return [ast.unparse(container)]
    return []


def _region_assignment(node):
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return []
    target = node.targets[0]
    if not isinstance(target, ast.Name) or "region" not in target.id.lower():
        return []
    value = node.value
    if not isinstance(value, (ast.Tuple, ast.List, ast.Set)):
        return []
    out = []
    for item in value.elts:
        name = _ast_attr(item)
        if name:
            out.append(name)
        else:
            text = _str_constant(item)
            if text:
                out.append(text)
    return out


def scan_file(path: str, display_path: str):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        source = fh.read()
    try:
        tree = ast.parse(source, filename=display_path)
    except SyntaxError:
        return [], {"path": display_path, "sha256": sha256_text(source), "error": "syntax"}
    file_sha = sha256_text(source)
    rules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            for symbol in _isinstance_types(node.test):
                rules.append((node.lineno, "isinstance_ast", symbol, ast.unparse(node.test)))
            for symbol in _class_name_tests(node.test):
                rules.append((node.lineno, "class_name_eq", symbol, ast.unparse(node.test)))
            for symbol in _opcode_tests(node.test):
                rules.append((node.lineno, "opcode_eq", symbol, ast.unparse(node.test)))
        elif isinstance(node, ast.Assign):
            for symbol in _region_assignment(node):
                rules.append((node.lineno, "region_type", symbol, ast.unparse(node)))
    seen = set()
    out = []
    for line, kind, symbol, pattern in rules:
        key = (line, kind, symbol)
        if key in seen:
            continue
        seen.add(key)
        anchor = "%s:%d" % (display_path, line)
        rule_id = "RULE-" + sha256_text("%s|%s|%s" % (anchor, kind, symbol))[:12]
        out.append({
            "rule_id": rule_id, "anchor": anchor, "file": display_path,
            "line": line, "kind": kind, "symbol": symbol,
            "pattern": pattern, "source_sha256": file_sha,
        })
    return out, {"path": display_path, "sha256": file_sha, "rules": len(out)}


def build_universe(code_root: str):
    files = sorted(glob.glob(os.path.join(code_root, "**", "*.py"), recursive=True))
    rules, per_file = [], []
    for path in files:
        try:
            rel = os.path.relpath(path, os.getcwd())
        except ValueError:
            rel = os.path.abspath(path)
        rel = rel.replace("\\", "/")
        found, meta = scan_file(path, rel)
        rules.extend(found)
        per_file.append(meta)
    rules.sort(key=lambda item: (item["file"], item["line"], item["kind"], item["symbol"]))
    groups = collections.OrderedDict()
    for item in rules:
        key = (item["kind"], item["symbol"])
        group = groups.get(key)
        if group is None:
            group = {
                "rule_id": "RULE-" + sha256_text("%s|%s" % key)[:12],
                "anchor": item["anchor"], "anchors": [], "file": item["file"],
                "line": item["line"], "kind": item["kind"], "symbol": item["symbol"],
                "pattern": item["pattern"], "patterns": [], "source_sha256": item["source_sha256"],
                "source_files": [], "occurrences": 0,
            }
            groups[key] = group
        group["anchors"].append(item["anchor"])
        if item["pattern"] not in group["patterns"]:
            group["patterns"].append(item["pattern"])
        if item["file"] not in group["source_files"]:
            group["source_files"].append(item["file"])
        group["occurrences"] += 1
    universe = list(groups.values())
    universe.sort(key=lambda item: (item["kind"], item["symbol"]))
    counts = collections.Counter(item["kind"] for item in universe)
    return {
        "tool": "rule_universe", "version": TOOL_VERSION,
        "scanner_sha256": sha256_text(open(__file__, "rb").read().decode("utf-8", "replace")),
        "code_root": code_root, "files": per_file,
        "total_rules": len(universe), "total_occurrences": len(rules),
        "counts_by_kind": dict(sorted(counts.items())),
        "rules": universe,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="independent core/cfg rule universe")
    parser.add_argument("--code", default="core/cfg")
    parser.add_argument("--json", default="")
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    args = parser.parse_args(argv)
    data = build_universe(args.code)
    if args.json:
        directory = os.path.dirname(os.path.abspath(args.json))
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
    print("[rule_universe] total_rules=%d files=%d kinds=%s"
          % (data["total_rules"], len(data["files"]), json.dumps(data["counts_by_kind"], ensure_ascii=False)))
    return 0 if data["total_rules"] > 0 else 2


if __name__ == "__main__":
    sys.exit(main())
