#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent rule-universe enumerator for G4 (Task 9.4).

The universe is derived statically from core/cfg/** dispatch branches:

  * isinstance(x, ast.X) branches
  * opname/opcode/name == "X" branches
  * node.__class__.__name__ == "X" branches
  * region-type tuple/list assignments

It never reads rule_manifest.json.  Manifest mapping is a separate step.

Measurement scope (revision 1.1.0)
----------------------------------
An opcode-keyed branch (``opname == 'BINARY_ADD'``) can only fire on a code
object that actually carries that opcode.  On CPython 3.11 ``BINARY_ADD`` is
not a real opcode name (``dis.opmap`` has ``BINARY_OP``), so such a branch is
*not exercisable* by any 3.11 corpus: it can never be witnessed true or
false, and counting it in the denominator makes ``open = 0`` unsatisfiable by
construction rather than by capability.

``--opcode-scope interpreter`` therefore separates those branches into
``excluded_rules`` with a machine-checkable reason and the evidence used
(``members`` resolved through module-level opcode-name tuples, plus
``dis.opmap``).  Nothing is deleted: excluded entries keep rule_id, anchor and
pattern, and ``rules`` + ``excluded_rules`` always covers every enumerated
branch.  The default stays ``any`` (no filter), so the unfiltered universe is
still reproducible.

CLI:
    python -X utf8 tools/completeness/rule_universe.py --code core/cfg \
        --json .trae/specs/attack-completeness-claims/rounds/round9/rule_universe.json
"""

from __future__ import annotations

import argparse
import ast
import collections
import dis
import re
import glob
import hashlib
import json
import os
import sys

TOOL_VERSION = "1.1.1"
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



def _module_opcode_sets(tree):
    """模块级 UPPERCASE 名字 -> 字符串常量元组（操作码名集合的解析表）。"""
    sets = {}
    for node in tree.body if hasattr(tree, "body") else []:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not target.id.isupper():
            continue
        value = node.value
        # frozenset({...}) / frozenset((...)) / set([...]) / tuple((...)) 一层解包
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) \
                and value.func.id in ("frozenset", "set", "tuple", "list") and len(value.args) == 1:
            value = value.args[0]
        if not isinstance(value, (ast.Tuple, ast.List, ast.Set)):
            continue
        names = [_str_constant(item) for item in value.elts]
        names = [n for n in names if n]
        if names and len(names) == len(value.elts):
            sets.setdefault(target.id, names)
    return sets


_BARE_OPCODE_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")


def scope_rules(universe, opcode_sets, opmap):
    """把 opcode 键规则按解释器作用域切分：可触发 / 不可触发（附证据）。"""
    kept, excluded = [], []
    for rule in universe:
        sym = rule.get("symbol") or ""
        if rule.get("kind") != "opcode_eq":
            kept.append(rule)
            continue
        resolved = opcode_sets.get(sym)
        if resolved:
            members = list(resolved)
        elif sym in opmap:
            members = [sym]
        elif _BARE_OPCODE_NAME.match(sym):
            members = [sym]
        else:
            kept.append(rule)          # AST 标记 / 字面量：与操作码无关，保留
            continue
        live = [m for m in members if m in opmap]
        if live:
            kept.append(rule)
            continue
        item = dict(rule)
        item["excluded_reason"] = "no_member_in_interpreter_opmap"
        item["members"] = members
        item["interpreter"] = "%d.%d.%d" % sys.version_info[:3]
        excluded.append(item)
    return kept, excluded

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


def build_universe(code_root: str, opcode_scope: str = "any"):
    files = sorted(glob.glob(os.path.join(code_root, "**", "*.py"), recursive=True))
    rules, per_file = [], []
    opcode_sets = {}
    for path in files:
        try:
            rel = os.path.relpath(path, os.getcwd())
        except ValueError:
            rel = os.path.abspath(path)
        rel = rel.replace("\\", "/")
        found, meta = scan_file(path, rel)
        rules.extend(found)
        per_file.append(meta)
        try:
            with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
                opcode_sets.update(_module_opcode_sets(ast.parse(fh.read())))
        except SyntaxError:
            pass
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
    excluded_rules = []
    if opcode_scope == "interpreter":
        universe, excluded_rules = scope_rules(universe, opcode_sets, set(dis.opmap))
    counts = collections.Counter(item["kind"] for item in universe)
    return {
        "tool": "rule_universe", "version": TOOL_VERSION,
        "opcode_scope": opcode_scope,
        "interpreter": "%d.%d.%d" % sys.version_info[:3],
        "excluded_count": len(excluded_rules),
        "excluded_rules": excluded_rules,
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
    parser.add_argument("--opcode-scope", default="any", choices=["any", "interpreter"],
                        help="interpreter: 把操���码名在本解释器 dis.opmap 里全不存在的分支移入 excluded_rules")
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    args = parser.parse_args(argv)
    data = build_universe(args.code, args.opcode_scope)
    if args.json:
        directory = os.path.dirname(os.path.abspath(args.json))
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
    print("[rule_universe] total_rules=%d excluded=%d scope=%s files=%d kinds=%s"
          % (data["total_rules"], data.get("excluded_count", 0), data.get("opcode_scope", "any"),
             len(data["files"]), json.dumps(data["counts_by_kind"], ensure_ascii=False)))
    return 0 if data["total_rules"] > 0 else 2


if __name__ == "__main__":
    sys.exit(main())
