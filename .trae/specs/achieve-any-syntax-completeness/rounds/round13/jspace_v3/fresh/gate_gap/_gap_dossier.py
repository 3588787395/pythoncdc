#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the G4 "unreachable rule" dossier evidence pack (evidence only).

Read-only: reads the universe / coverage / executed-line data and the source
tree; writes only into fresh/gate_gap/ and D:/temp/opencode/cl_layout/gap/.
It never edits a rule's status / witnesses / semantic_domain / proof /
composition, and never rewrites the universe.

    python -I -X utf8 _gap_dossier.py \
        --universe <universe_v2.json> --coverage <coverage_v2.json> \
        --exec <gap_exec_v2.json> --out-json <g4_unreachable.json> \
        --out-md <G4_UNREACHABLE_DOSSIER.md>
"""
from __future__ import annotations

import argparse
import ast
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "site-packages", ".canary-private",
             ".canary-work", ".trae", ".obsidian", ".workbuddy", "_work"}


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


def rel(root, path):
    return os.path.relpath(path, root).replace("\\", "/")


def read_text(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        return fh.read()


class ScopeIndex:
    """Innermost enclosing function / owning class for every source line."""

    def __init__(self):
        self.by_file = {}
        self.classes = {}
        self.src_lines = {}
        self.tree = {}

    def add_file(self, root, path):
        relpath = rel(root, path)
        src = read_text(path)
        try:
            tree = ast.parse(src, filename=relpath)
        except SyntaxError:
            return
        self.tree[relpath] = tree
        scopes = []
        classes = []

        def walk(node, prefix):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = "%s%s" % (prefix, child.name)
                    scopes.append({
                        "qualname": name,
                        "name": child.name,
                        "lineno": child.lineno,
                        "end_lineno": getattr(child, "end_lineno", child.lineno),
                    })
                    walk(child, name + ".")
                elif isinstance(child, ast.ClassDef):
                    classes.append({
                        "qualname": prefix + child.name,
                        "name": child.name,
                        "lineno": child.lineno,
                        "end_lineno": getattr(child, "end_lineno", child.lineno),
                    })
                    walk(child, prefix + child.name + ".")
                else:
                    walk(child, prefix)

        walk(tree, "")
        scopes.sort(key=lambda s: (s["lineno"], s["end_lineno"]))
        self.by_file[relpath] = scopes
        self.classes[relpath] = classes
        self.src_lines[relpath] = src.splitlines()

    def innermost(self, relpath, line):
        best = None
        for scope in self.by_file.get(relpath, []):
            if scope["lineno"] <= line <= scope["end_lineno"]:
                if best is None or (scope["lineno"] >= best["lineno"]
                                    and scope["end_lineno"] <= best["end_lineno"]):
                    best = scope
        return best

    def class_of(self, relpath, qualname):
        best = None
        for item in self.classes.get(relpath, []):
            if qualname.startswith(item["qualname"] + "."):
                if best is None or len(item["qualname"]) > len(best["qualname"]):
                    best = item
        return best

    def source_at(self, relpath, line):
        lines = self.src_lines.get(relpath) or []
        if 1 <= line <= len(lines):
            return lines[line - 1].strip()
        return ""


def module_of(relpath):
    return relpath[:-3].replace("/", ".") if relpath.endswith(".py") else relpath


def collect_imports(root, paths):
    """Every import edge in the given files (module level or lazy)."""
    edges = []
    for path in paths:
        relpath = rel(root, path)
        try:
            tree = ast.parse(read_text(path), filename=relpath)
        except SyntaxError:
            continue
        funcs = [{"name": n.name, "lineno": n.lineno,
                  "end": getattr(n, "end_lineno", n.lineno)}
                 for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        funcs.sort(key=lambda s: (s["lineno"], s["end"]))

        def targets(node):
            if isinstance(node, ast.Import):
                return [("PLAIN", alias.name, [], node.lineno) for alias in node.names]
            if isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    pkg = os.path.dirname(relpath).replace("/", ".")
                    parts = pkg.split(".") if pkg else []
                    if node.level > 1:
                        parts = parts[:-(node.level - 1)] if node.level - 1 else parts
                    base = ".".join([p for p in parts if p] + ([base] if base else []))
                return [("FROM", base, [a.name for a in node.names], node.lineno)]
            return []

        for node in ast.walk(tree):
            found = targets(node)
            if not found:
                continue
            owner = None
            for scope in funcs:
                if scope["lineno"] <= node.lineno <= scope["end"]:
                    if owner is None or scope["lineno"] >= owner["lineno"]:
                        owner = scope
            for _, base, names, lineno in found:
                edges.append({"file": relpath, "lineno": lineno, "base": base,
                              "names": names, "lazy": owner is not None,
                              "owner": owner["name"] if owner else None})
    return edges


def import_closure(seeds, edges, known_modules):
    """BFS over module import edges: what does each module pull in at import time."""
    by_file = collections.defaultdict(list)
    for edge in edges:
        by_file[module_of(edge["file"])].append(edge)
    reached = {}
    queue = collections.deque()
    for seed in seeds:
        if seed not in reached:
            reached[seed] = {"via": "<pycdc.py seed>", "lineno": 0, "lazy": False, "owner": None}
            queue.append(seed)
    while queue:
        mod = queue.popleft()
        for edge in by_file.get(mod, []):
            candidates = [edge["base"]] + [edge["base"] + "." + n for n in edge["names"]]
            for name in candidates:
                if name in known_modules and name not in reached:
                    reached[name] = {"via": edge["file"], "lineno": edge["lineno"],
                                     "lazy": edge["lazy"], "owner": edge["owner"]}
                    queue.append(name)
    return reached


MECH = {
    "ObjectivePatchDetector.analyze_file":
        "`objective_patch_detector.py` on 131 J pycs executed **0 lines**; it has 0 importers in "
        "`core/` (the only references are `scripts/phase6_final_test.py:7`, "
        "`scripts/run_baseline_detection.py:20` and the module's own `__main__` self-import at "
        "`objective_patch_detector.py:15`) -> the module is not on the `pycdc.py` call chain.",
    "ObjectivePatchDetector._extract_test_pattern":
        "Same cluster: `objective_patch_detector.py` executed 0 lines and has no `core/` importer; "
        "its only call site `objective_patch_detector.py:182` sits inside `analyze_file`, which "
        "also executed 0 lines.",
    "ObjectivePatchDetector._node_signature":
        "Same cluster; the call site `objective_patch_detector.py:181` is inside "
        "`_check_d2_special_branches`, which executed 0 lines.",
    "ObjectivePatchDetector._check_d2_special_branches":
        "Same cluster: no `core/` importer, module executed 0 lines.",
    "P1Detector._is_local_region_var":
        "`patch_detector.py` executed **0 lines** and has 0 importers in `core/` "
        "(`grep -rn patch_detector core/` only hits the sub-string inside "
        "`objective_patch_detector`) -> a standalone detector module, not on the decompile chain.",
    "P2Detector._extract_opname_strings":
        "Same cluster: `patch_detector.py` executed 0 lines, no `core/` importer.",
    "StructuredAnalyzer._identify_with_structures":
        "`structured_analyzer.py` executed **0 lines**; its importers are only the package barrel "
        "`core/cfg/__init__.py:66`, legacy `ast_generator_v2.py:14` (the `ASTGeneratorV2` class body "
        "itself executed 0 lines) and `exception_handler.py:14` (that module also executed 0 lines) "
        "-> no live user. The `StructuredAnalyzer()` construction point "
        "`ast_generator_v2.py:3508` never executed; the region pipeline never builds the class.",
    "StructuredAnalyzer._identify_try_except_pre_311":
        "Same cluster: `structured_analyzer.py` executed 0 lines and the construction point never ran.",
    "_find_handler_type_load":
        "`exception_handler.py` executed **0 lines**; its only `core/` importer is the lazy import "
        "at `structured_analyzer.py:11717`, and `structured_analyzer` itself executed 0 lines -> a "
        "chained dead region.",
    "CodeGenerator._generate_dict_node":
        "`CodeGenerator.generate()` (`code_generator.py:110`) only calls `_generate_dict_node` when "
        "`isinstance(node, dict)` (`code_generator.py:133`); the tracer passes the `ASTNode` returned "
        "by `CFGASTConverter().convert(...)`, and the dict fallback inside `_generate_node()` "
        "(`code_generator.py:185`) never fires either -> all 212 lines of the function executed 0 "
        "lines, and all 20 call sites of `_generate_dict_node` are inside it. Contrast: the "
        "**expression-level** dict entry `_generate_expression` (`code_generator.py:3778`, also "
        "`isinstance(node, dict)`) *is* live (155 lines executed), so dict nodes do reach the code "
        "generator - what is dead is the **statement-level** entry "
        "`generate(dict)` / `_generate_node(dict)`. The `CodeGenerator` class itself is live (1464 "
        "lines of the same file executed) and `CFGCodeGenerator` is only an alias "
        "(`code_generator.py:6715`).",
    "ASTGeneratorV2._generate_if_ast":
        "The `ASTGeneratorV2` class executed **0 lines** on the J trace (all 1209 executed lines of "
        "`ast_generator_v2.py` belong to `ExpressionReconstructor`); every caller of "
        "`_generate_if_ast` is another `ASTGeneratorV2` method "
        "(`ast_generator_v2.py:9197/9268/9299/...`), none of which executed -> the class is never "
        "constructed. The region pipeline only takes `ExpressionReconstructor` from this module "
        "(`region_ast_generator.py:236`).",
    "ASTGeneratorV2._generate_entry_sequence": "Same cluster: the `ASTGeneratorV2` class executed 0 lines.",
    "ASTGeneratorV2._remove_unreachable_code": "Same cluster: the `ASTGeneratorV2` class executed 0 lines.",
    "ASTGeneratorV2._generate_block_content_skip_iterator":
        "Same cluster: the `ASTGeneratorV2` class executed 0 lines.",
    "ASTGeneratorV2._generate_if_ast.extract_elif_chain":
        "Nested function of `_generate_if_ast` (`ast_generator_v2.py:13416`); its only call site "
        "`ast_generator_v2.py:13894` is inside the 0-line parent function -> doubly unreachable.",
    "ASTGeneratorV2._extract_function_args": "Same cluster: the `ASTGeneratorV2` class executed 0 lines.",
    "ASTGeneratorV2._extract_iterator_v2": "Same cluster: the `ASTGeneratorV2` class executed 0 lines.",
    "ASTGeneratorV2._extract_with_context": "Same cluster: the `ASTGeneratorV2` class executed 0 lines.",
    "ASTGeneratorV2._generate_comprehension_function":
        "Same cluster: the `ASTGeneratorV2` class executed 0 lines.",
    "ASTGeneratorV2._generate_inner_while_from_block":
        "Same cluster: the `ASTGeneratorV2` class executed 0 lines.",
    "ASTGeneratorV2._has_terminal_statement": "Same cluster: the `ASTGeneratorV2` class executed 0 lines.",
    "ASTGeneratorV2._process_instruction_sequence":
        "Same cluster: the `ASTGeneratorV2` class executed 0 lines.",
    "ExpressionReconstructor._extract_comp_elt":
        "Same module (`ast_generator_v2.py` is live), but this comprehension-element side path "
        "executed 0 of its 88 lines and none of its call sites executed.",
    "RegionAnalyzer._extract_with_items._parse_bind_unpack":
        "Parser for `with ... as (a, b)` bind-unpacking; the module is live (`region_analyzer.py` "
        "has 16045 executed lines) but this nested function executed 0/44 lines -> no with-target "
        "was ever an unpacking form.",
    "RegionASTGenerator._build_ternary_boolop_condition":
        "Ternary/boolop condition side path; the function executed 0/171 lines while the module is live.",
    "RegionASTGenerator._generate_return_ast":
        "The `return`-statement reconstruction side path executed 0/122 lines while the module is live.",
    "RegionASTGenerator._build_multi_target_del_targets":
        "The `del a, b` multi-target side path executed 0/88 lines while the module is live.",
    "BasicBlock.is_conditional":
        "The `conditional_ops` set arm at `basic_block.py:193` lives in `BasicBlock.is_conditional`, "
        "which executed 0/23 lines **and has 0 call sites in `core/`** (caller-refs 0), although "
        "`basic_block.py` has 47 executed lines in other methods.",
}

D3_SHAPE = {
    "CodeGenerator._generate_expression":
        "a dict `FunctionObject` node (lambda / genexpr value) whose `code` field is itself a dict "
        "`CodeObject`: the `'<genexpr>'` branch needs a `closure` Tuple, the `'<lambda>'` branch "
        "renders a placeholder (`code_generator.py:4085-4098`). `_generate_expression` already "
        "executed 155/527 lines and its dict entry (`code_generator.py:3778`) did fire, so dict "
        "expression nodes do arrive; but the region pipeline normally rewrites FunctionObjects into "
        "`Lambda` via `_convert_lambda_function_objects` (`region_ast_generator.py:33688`), so this "
        "arm only fires for a shape that survives that conversion. Not yet demonstrated.",
    "RegionASTGenerator._loop_handle_header":
        "a loop header whose prefix contains `IS_OP/IS_NOT/NOT_OP/UNARY_NOT` "
        "(`while x is not y:` / `while not f():`) and ends with an assignment statement.",
    "RegionAnalyzer._is_except_break_exit":
        "try/except inside a loop where the handler ends with `break` after `POP_EXCEPT` "
        "(`PURE_JUMP_OPS`/`POP_BLOCK`).",
    "RegionASTGenerator._generate_try":
        "a nested outer-try handler block containing `CHECK_EXC_MATCH`/`CHECK_EG_MATCH` "
        "(`except E as e:` type matching).",
    "RegionASTGenerator._generate_boolop_impl":
        "a boolop whose prefix instructions contain `STORE_*` (the `flag = a and b` shape where the "
        "prefix stores an intermediate value before the expression is rebuilt).",
    "RegionASTGenerator._build_chained_complex_target_assign":
        "chained complex target assignment `a.b = c[d] = expr` (several non-name targets).",
    "RegionASTGenerator._b33_await_owner_merged_stmts":
        "`async with a() as x, b() as y:` (merged multi-owner with a noise instruction run).",
    "ComprehensionGenerator._b247_mixed_boolchain":
        "a mixed and/or boolean chain (`a and b or c`) in a comprehension / ternary context.",
    "RegionASTGenerator._try_build_ternary_operand_chained_compare":
        "a conditional expression whose operand is a chained compare (`x if a < b < c else y`).",
    "ComprehensionGenerator.try_generate_comprehension_assign":
        "a comprehension assignment `x = [i for i in y]` whose code object instruction stream hits "
        "the `_cso` set.",
    "RegionASTGenerator._b86_complete_with_items":
        "a `with` target that is an attribute/subscript (`with a() as obj.attr:`).",
    "ComprehensionGenerator._find_returns_pending_value_successor":
        "a tail-of-body return whose value needs frame bookkeeping instructions "
        "(`PUSH_NULL`/`CACHE`).",
    "RegionASTGenerator._generate_handler_body_statements":
        "an except body whose prefix contains noise instructions (`RESUME`/`POP_TOP`, ...).",
    "ComprehensionGenerator._value_chain_key_split_point":
        "a value chain with an unconditional jump in the middle of the key split.",
    "RegionASTGenerator._build_multi_target_unpack":
        "multi-target unpacking `a, b = c = ...` or `(a, b), c = ...`.",
    "RegionASTGenerator._generate_loop":
        "`x = yield from it` (the STORE that closes a yield-from).",
    "RegionASTGenerator._build_boolop_augassign_target":
        "boolop augmented assignment to an attribute/subscript target: "
        "`obj.attr += a and b` / `obj[k] += a and b`.",
}


def ev_line(r):
    """One-line grep-style evidence for a single rule."""
    return ("%s | %s:%d | sym=%s | scope=%s (%d/%d lines executed) | importers: consumer=%d "
            "barrel=%d cli=%d | caller-refs %d (executed %d) | pycdc-closure=%s | %s/%s"
            % (r["rule_id"], r["file"], r["line"], r["symbol"], r["scope"],
               r["scope_lines_executed"], r["scope_lines_total"] or 0,
               len(r["importers_in_core"]), len(r["importers_barrel"]),
               len(r["importers_cli"]), r["refs_total"], r["refs_executed"],
               "yes" if r["in_pycdc_import_closure"] else "no",
               r["tier"], r["tier_kind"]))


def code_refs(r, limit=2):
    """Call sites that look like code (skip comment-only matches)."""
    refs = [x for x in r["refs_top"] if not x["text"].lstrip().startswith("#")]
    return refs[:limit]


def head_sha(root):
    try:
        import subprocess
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=root, text=True).strip()
    except Exception:
        return "(unknown)"


def render_md(payload, universe, coverage, execdata):
    rules = payload["rules"]
    t1 = [r for r in rules if r["tier"] == "D1"]
    t2 = [r for r in rules if r["tier"] == "D2"]
    t3 = [r for r in rules if r["tier"] == "D3"]
    out = []
    w = out.append

    w("# G4 unreachable-rule dossier (D1 / D2 / D3)")
    w("")
    w("> **Evidence only.** `core/`, `scripts/`, `tests/`, `tools/completeness/*.py` were not "
      "modified. No `status` / `witnesses` / `semantic_domain` / `proof` / `composition` field was "
      "touched, and no `rule_universe` file was rewritten (this round creates new `universe_v2.json` / "
      "`manifest_v2.json` / `traces_v2.json` / `coverage_v2.json`). `judgment_space.json`, "
      "`rule_universe_current.json` and `rule_traces_current.json` are read-only inputs.")
    w("")
    w("## 0. Reading: the new authoritative baseline (current HEAD)")
    w("")
    w("The same command set as `fresh/g4_audit/G4_CURRENT.md`, re-run against the current tree "
      "(cwd = `F:\\Downloads\\pythoncdc-main`):")
    w("")
    w("```powershell")
    w("python -I -X utf8 tools/completeness/rule_universe.py --code core/cfg \\")
    w("  --json fresh/gate_gap/universe_v2.json")
    w("python -I -X utf8 tools/completeness/rule_manifest.py --generate \\")
    w("  --universe fresh/gate_gap/universe_v2.json --manifest fresh/gate_gap/manifest_v2.json")
    w("python -I -X utf8 .../fresh/g4_audit/trace_g4_current.py \\")
    w("  --universe fresh/gate_gap/universe_v2.json \\")
    w("  --jspace .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \\")
    w("  --out fresh/gate_gap/traces_v2.json")
    w("python -I -X utf8 tools/completeness/rule_manifest.py --check \\")
    w("  --universe fresh/gate_gap/universe_v2.json --manifest fresh/gate_gap/manifest_v2.json \\")
    w("  --jspace .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \\")
    w("  --traces fresh/gate_gap/traces_v2.json --json fresh/gate_gap/coverage_v2.json")
    w("```")
    w("")
    w("| metric | old (2026-10-27, stale) | **new (current HEAD)** |")
    w("|---|---:|---:|")
    w("| independent rules | 342 | **%d** |" % payload["total_rules"])
    w("| branch positions | 5791 | **%d** |" % universe.get("total_occurrences", 0))
    w("| `isinstance_ast` / `opcode_eq` | 15 / 327 | **%s / %s** |"
      % (universe["counts_by_kind"].get("isinstance_ast"),
         universe["counts_by_kind"].get("opcode_eq")))
    w("| `rules_hit` | 243 | **%d** |" % (payload["total_rules"] - payload["empty_cov"]))
    w("| `empty_cov` (never hit by the J space) | 99 | **%d** |" % payload["empty_cov"])
    w("| `unmapped` / `orphan` / `anchor_orphans` | 0 / 0 / 0 | **0 / 0 / 0** |")
    w("| `proved` / `open` | 0 / 342 | **0 / %d** |"
      % coverage.get("open", payload["total_rules"]))
    w("| G4 | FAIL | **FAIL** (`mapping_or_proof_gap`) |")
    w("")
    w("Measured at HEAD `%s` (2026-11-17); the old column is the 2026-10-27 reading whose "
      "line anchors have since drifted." % head_sha(os.getcwd()))
    w("")
    w("Trace summary: `entries=%d` (unique pycs=%d) `failed=%d`. The %d rules below are exactly the "
      "ones whose `coverage[rule_id] == []` in `coverage_v2.json`."
      % (sum(len(v.get("entries") or []) for v in (execdata.get("per_pyc") or {}).values()),
         execdata["summary"].get("pycs", execdata["summary"]["traced"]),
         execdata["summary"]["failed"], payload["empty_cov"]))
    w("")
    w("### Runtime evidence behind the tiering")
    w("")
    w("`_gap_exec.py` replays exactly the same pipeline as `trace_g4_current.py` (`build_cfg` -> "
      "`RegionASTGenerator` -> `CFGASTConverter` -> `CFGCodeGenerator` over the 131 J pycs) but "
      "records the **executed line set per file** (`--out .../gap_exec_v2.json`):")
    w("")
    w("```text")
    for k, v in payload["files_executed_lines"].items():
        w("  %-46s %6d lines" % (k, v))
    w("```")
    w("")
    w("`core/cfg/{structured_analyzer,objective_patch_detector,patch_detector,"
      "patch_detector_enhanced,exception_handler}.py` are **absent** from that table, i.e. those "
      "modules executed **0 lines** on the J trace.")
    w("")
    w("Static import reachability from `pycdc.py` is *not* the discriminator, because "
      "`core/cfg/__init__.py` re-exports these modules: `from core.cfg import build_cfg` "
      "(`pycdc.py:83`) runs the package barrel, so almost every module is import-reachable. "
      "The decisive fact is whether any line of the module **executed**:")
    w("")
    w("| file | in `pycdc.py` import closure | reached via | executed lines |")
    w("|---|---|---|---:|")
    per_file_rows = collections.defaultdict(lambda: {"n": 0, "closure": False, "via": None})
    for r in rules:
        row = per_file_rows[r["file"]]
        row["n"] += 1
        row["closure"] = row["closure"] or r["in_pycdc_import_closure"]
        row["via"] = row["via"] or r["closure_via"]
    for f in sorted(per_file_rows):
        row = per_file_rows[f]
        via = row["via"]
        via_txt = ("`%s:%s`%s" % (via["via"], via["lineno"],
                                  " (lazy)" if via.get("lazy") else "")) if via else "-"
        w("| `%s` | %s | %s | %d |"
          % (f, "yes" if row["closure"] else "**no**", via_txt,
             payload["files_executed_lines"].get(f, 0)))
    w("")
    w("## 1. Tier decision rule (mechanically re-computable)")
    w("")
    w("| tier | criterion | meaning |")
    w("|---|---|---|")
    w("| **D1** | the rule's file executed **0 lines**, and there is no consumer importer in `core/` "
      "(only the package barrel `core/cfg/__init__.py`, CLI scripts, or legacy modules that "
      "themselves executed 0 lines) | module-level dead region: no tracer can enter it without "
      "changing the product call chain or the universe |")
    w("| **D2** | module is live (has executed lines) but the rule's enclosing function/method "
      "executed **0 lines** | imported, but never constructed / entered at runtime |")
    w("| **D3** | the rule's enclosing function **has executed lines** but the rule's branch line "
      "did not | the function is reachable; what is missing is an input shape that triggers the branch |")
    w("")
    w("Per-rule fields in `g4_unreachable.json`: `importers_in_core` / `importers_barrel` / "
      "`importers_cli` / `importers[*].executed` (did that import statement line execute) / "
      "`refs_total` / `refs_executed` (did any call site of the function execute) / "
      "`scope_lines_executed` / `scope_lines_total` / `class_lines_executed` / "
      "`in_pycdc_import_closure` / `closure_via`.")
    w("")
    w("## 2. Summary")
    w("")
    w("| tier | rules | files | criterion mix |")
    w("|---|---:|---:|---|")
    for tier, rows in (("D1", t1), ("D2", t2), ("D3", t3)):
        kinds = collections.Counter(r["tier_kind"] for r in rows)
        files = len({r["file"] for r in rows})
        w("| **%s** | **%d** | %d | %s |"
          % (tier, len(rows), files,
             ", ".join("`%s` x%d" % (k, v) for k, v in kinds.most_common())))
    w("| total | **%d** | %d | %.1f%% of the universe |"
      % (len(rules), len({r["file"] for r in rules}),
         100.0 * len(rules) / max(1, payload["total_rules"])))
    w("")
    w("By file:")
    w("")
    w("| file | D1 | D2 | D3 | total |")
    w("|---|---:|---:|---:|---:|")
    per_file = collections.defaultdict(collections.Counter)
    for r in rules:
        per_file[r["file"]][r["tier"]] += 1
    for f in sorted(per_file, key=lambda x: -sum(per_file[x].values())):
        c = per_file[f]
        w("| `%s` | %d | %d | %d | **%d** |"
          % (f, c.get("D1", 0), c.get("D2", 0), c.get("D3", 0), sum(c.values())))
    w("")
    w("## 3. D1 list (%d rules, module-level dead region)" % len(t1))
    w("")
    w("### 3.1 Clusters and mechanism")
    w("")
    seen = set()
    for r in t1:
        key = (r["file"], r["scope"])
        if key in seen:
            continue
        seen.add(key)
        n = sum(1 for x in t1 if (x["file"], x["scope"]) == key)
        w("- **`%s` / `%s` (%d rules)** - %s"
          % (r["file"], r["scope"], n, MECH.get(r["scope"], "(no note)")))
    w("")
    w("### 3.2 Per-rule evidence lines")
    w("")
    for r in t1:
        w("- `" + ev_line(r) + "`")
        for ref in code_refs(r):
            w("  - ref: `%s:%d` (executed=%s) `%s`"
              % (ref["file"], ref["lineno"], "yes" if ref["executed"] else "no",
                 ref["text"][:110]))
    w("")
    w("## 4. D2 list (%d rules, module live but function/method never entered)" % len(t2))
    w("")
    w("### 4.1 Clusters and mechanism")
    w("")
    seen = set()
    for r in t2:
        key = (r["file"], r["scope"])
        if key in seen:
            continue
        seen.add(key)
        n = sum(1 for x in t2 if (x["file"], x["scope"]) == key)
        w("- **`%s` / `%s` (%d rules)** - %s"
          % (r["file"], r["scope"], n, MECH.get(r["scope"], "(no note)")))
    w("")
    w("### 4.2 Per-rule evidence lines")
    w("")
    for r in t2:
        w("- `" + ev_line(r) + "`")
        refs = code_refs(r, 1)
        if refs:
            ref = refs[0]
            w("  - first code call site: `%s:%d` (executed=%s) `%s`"
              % (ref["file"], ref["lineno"], "yes" if ref["executed"] else "no",
                 ref["text"][:110]))
    w("")
    w("## 5. D3 list (%d rules, reachable but needs a new input shape)" % len(t3))
    w("")
    w("These functions **did execute** (`scope_lines_executed > 0`), so they cannot be excluded as "
      "unreachable; what is missing is a J entry that triggers the branch. The shapes below are "
      "**hypotheses inferred from the branch guard** and have not yet been proven by a probe.")
    w("")
    w("| rule | location | scope | executed lines | candidate input shape (unverified) |")
    w("|---|---|---|---:|---|")
    for r in t3:
        w("| `%s` | `%s:%d` | `%s` | %d/%d | %s |"
          % (r["rule_id"], r["file"], r["line"], r["scope"],
             r["scope_lines_executed"], r["scope_lines_total"] or 0,
             D3_SHAPE.get(r["scope"], "(no note)")))
    w("")
    w("## 6. Route A / Route B scale estimates (not executed)")
    w("")
    w("### Route A: extend the tracer to the legacy / CLI paths")
    w("")
    w("**What to change** (`fresh/g4_audit/trace_g4_current.py`, about +10 lines):")
    w("")
    w("1. For every pyc, reuse the **same `cfg`** and additionally run the legacy pipeline: "
      "`legacy_ast = generate_ast_v2(cfg)` (`ast_generator_v2.py`'s "
      "`generate_ast_v2(cfg, recursive=True)` takes a `ControlFlowGraph`, not a code object) then "
      "`CodeGenerator().generate(legacy_ast)` (the dict entry at `code_generator.py:110/133`). "
      "`generate_ast_v2` constructs `ASTGeneratorV2`, whose `__init__` "
      "(`ast_generator_v2.py:3508`) constructs `StructuredAnalyzer`.")
    w("2. Optional: call `ObjectivePatchDetector().analyze_file(...)` / `P2Detector` explicitly "
      "(offline detectors).")
    w("3. Take the **union** of rule hits from both pipelines; the `records` schema of `traces_v2` "
      "stays unchanged.")
    w("4. Note `CFGCodeGenerator` is only an alias of `CodeGenerator` (`code_generator.py:6715`), so "
      "the dict entry and the current tracer entry are the **same class**; the only difference is "
      "whether a `dict` or an `ASTNode` is passed in.")
    w("")
    w("**Upper bound on rules saved** (must be measured, not promised):")
    w("")
    w("| sub-route | target rules | count | note |")
    w("|---|---|---:|---|")
    w("| A1 legacy decompile pipeline | `CodeGenerator._generate_dict_node` 16 + `ASTGeneratorV2.*` 32 "
      "+ `StructuredAnalyzer.*` 7 + `exception_handler._find_handler_type_load` 1 | **%d** | "
      "all unlocked by one `generate_ast_v2` entry |" % (16 + 32 + 7 + 1))
    w("| A2 offline detectors | `ObjectivePatchDetector.*` 11 + `P*Detector.*` 4 | **15** | only by "
      "explicitly invoking a detector that is not on the decompile path |")
    w("| A3 new input shapes | the D3 %d rules | **0** | a tracer change cannot help; new J entries "
      "are required |" % len(t3))
    w("")
    w("**Risks:**")
    w("")
    w("- Wording risk: the gate would move from \"the live `pycdc.py` path is covered\" to \"some "
      "pipeline touches it\", and legacy `ASTGeneratorV2`/`StructuredAnalyzer` are exactly the paths "
      "`pycdc.py` does not take - trading a wider input domain for a lower `empty_cov` weakens the "
      "completeness claim.")
    w("- Engineering risk: `ast_generator_v2.py` (27691 lines) and `structured_analyzer.py` (16096 "
      "lines) are legacy code and may raise or hang on 3.11 bytecode; the tracer wraps each entry in "
      "`try/except BaseException`, so any failure lands in `failed_entries` and the reading itself "
      "must be discounted.")
    w("- Domain risk: `patch_detector` / `objective_patch_detector` are **patch detectors**; running "
      "them only proves \"the detector runs\", not \"the decompile path is covered\".")
    w("- Bottom line: A1 can at best push `empty_cov` from %d down to %d (= D3); A1+A2 fully "
      "successful still leaves `empty_cov = %d`. **G4 stays FAIL** because `proved = 0`."
      % (payload["empty_cov"], len(t3), len(t3)))
    w("")
    w("### Route B: exclude D1/D2 from the universe by review")
    w("")
    w("**Evidence needed:** the per-rule evidence in this dossier (importer counts + executed lines "
      "+ call sites) plus reviewer sign-off. Note `rule_universe.py` has **no exclusion mechanism**: "
      "the universe is mechanically enumerated from the source "
      "(`tools/completeness/rule_universe.py:166-208`), so an \"exclusion\" requires introducing a "
      "`reviewed_exclusions` list into the tool or the universe - a tool change, out of scope for "
      "this read-only round.")
    w("")
    w("**After exclusion:**")
    w("")
    w("| scenario | universe | empty_cov | gate reading |")
    w("|---|---:|---:|---|")
    w("| current | %d | %d | FAIL `mapping_or_proof_gap` |"
      % (payload["total_rules"], payload["empty_cov"]))
    w("| exclude D1 (%d) | %d | %d | FAIL `mapping_or_proof_gap` |"
      % (len(t1), payload["total_rules"] - len(t1), payload["empty_cov"] - len(t1)))
    w("| exclude D1+D2 (%d) | %d | **%d** | FAIL `mapping_or_proof_gap` |"
      % (len(t1) + len(t2), payload["total_rules"] - len(t1) - len(t2), len(t3)))
    w("| exclude D1+D2+D3 (%d) | %d | **0** | **FAIL `not_all_proved`** |"
      % (payload["empty_cov"], payload["total_rules"] - payload["empty_cov"]))
    w("")
    w("**Can it PASS: no.** The last row is the decisive one: once `empty_cov` reaches 0, "
      "`rule_manifest.py --check` falls through to "
      "`elif ready != total: g4=\"FAIL\"; reason=\"not_all_proved\"` "
      "(`tools/completeness/rule_manifest.py:193-195`).")
    w("")
    w("### The missing item: proof / composition theory (neither the tracer nor the exclusion)")
    w("")
    w("The PASS criterion is `ready == total`, where `ready` counts only rules with "
      "`status == \"proved\"` that satisfy **all four** obligations "
      "(`rule_manifest.py:157-172`):")
    w("")
    w("1. `witnesses.positive` and `witnesses.negative` both non-empty, and every id present in the "
      "J space (`_witness_ok`, `rule_manifest.py:106-116`);")
    w("2. `semantic_domain.hosts` and `semantic_domain.depths` both non-empty "
      "(`_domain_ok`, `rule_manifest.py:119-124`);")
    w("3. `proof.proof_id` non-empty;")
    w("4. `composition` non-empty (`rule_manifest.py:163-165`).")
    w("")
    w("But `--generate` emits exactly the empty defaults for those four fields "
      "(`rule_manifest.py:49-76`: `semantic_domain={hosts:[],depths:[],note:\"not declared in v1\"}`, "
      "`witnesses={positive:[],negative:[]}`, `composition=[]`, `proof.proof_id=None`, "
      "`status=\"open\"`), and `proved` has been **0** in every historical reading "
      "(this round: 0 of %d, all `open`)." % payload["total_rules"])
    w("")
    w("So the missing item is the **per-rule semantic proof and composition obligation**: under "
      "which hosts/depths the rule holds (`semantic_domain`), positive and negative witnesses, a "
      "`proof_id` pointing at a checker, and the **composition** between rules (in the three stages "
      "region reduction -> AST generation -> code generation, how the output of rule A becomes the "
      "precondition of rule B). This round only closes the *reachability* half (which 100 rules are "
      "not executed and why); it does not close that half.")
    w("")
    w("## 7. Appendix: one evidence line per rule (%d rules, machine generated)" % len(rules))
    w("")
    w("```text")
    for r in rules:
        w(ev_line(r))
    w("```")
    w("")
    w("## 8. How to recompute")
    w("")
    w("```powershell")
    w("# executed lines (runtime evidence)")
    w("python -I -X utf8 fresh/gate_gap/_gap_exec.py \\")
    w("  --jspace .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \\")
    w("  --out D:/temp/opencode/cl_layout/gap/gap_exec_v2.json")
    w("# tiering + evidence lines + this document")
    w("python -I -X utf8 fresh/gate_gap/_gap_dossier.py \\")
    w("  --universe fresh/gate_gap/universe_v2.json \\")
    w("  --coverage fresh/gate_gap/coverage_v2.json \\")
    w("  --exec D:/temp/opencode/cl_layout/gap/gap_exec_v2.json \\")
    w("  --out-json fresh/gate_gap/g4_unreachable.json \\")
    w("  --out-md fresh/gate_gap/G4_UNREACHABLE_DOSSIER.md")
    w("```")
    w("")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="")
    parser.add_argument("--universe", required=True)
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--exec", dest="exec_path", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", default="")
    args = parser.parse_args(argv)
    root = repo_root(args.root or HERE)
    os.chdir(root)

    universe = load(args.universe)
    coverage = load(args.coverage)
    execdata = load(args.exec_path)
    cov = coverage["coverage"]
    union = {k: set(v) for k, v in (execdata.get("union") or {}).items()}

    all_py = []
    for base, dirs, files in os.walk(os.path.join(root, "core")):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(files):
            if name.endswith(".py"):
                all_py.append(os.path.join(base, name))
    scopes = ScopeIndex()
    for path in all_py:
        scopes.add_file(root, path)

    extra_py = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            p = os.path.join(base, name)
            r = rel(root, p)
            if r.startswith("core/") or r.startswith("scripts/") or r == "pycdc.py":
                extra_py.append(p)
    edges = collect_imports(root, extra_py)
    known_modules = {module_of(rel(root, p)) for p in extra_py}

    seeds = []
    for edge in edges:
        if edge["file"] != "pycdc.py":
            continue
        seeds.append(edge["base"])
        for n in edge["names"]:
            seeds.append((edge["base"] + "." + n) if edge["base"] else n)
    seeds = [m for m in dict.fromkeys(seeds) if m and m in known_modules]
    closure = import_closure(seeds, edges, known_modules)

    _imp_cache = {}

    def importers_of(relpath):
        if relpath in _imp_cache:
            return _imp_cache[relpath]
        mod = module_of(relpath)
        pkg = os.path.dirname(relpath).replace("/", ".")
        short = relpath[:-3].split("/")[-1]
        found = []
        for edge in edges:
            hit = (edge["base"] == mod
                   or (edge["base"] == pkg and short in edge["names"])
                   or edge["base"] == pkg + "." + short)
            if not hit or edge["file"] == relpath:
                continue
            found.append({"file": edge["file"], "lineno": edge["lineno"],
                          "lazy": edge["lazy"], "owner": edge["owner"],
                          "executed": edge["lineno"] in union.get(edge["file"], set()),
                          "text": scopes.source_at(edge["file"], edge["lineno"])})
        _imp_cache[relpath] = found
        return found

    _ref_cache = {}

    def refs_of_symbol(name, defining_file):
        key = (name, defining_file)
        if key in _ref_cache:
            return _ref_cache[key]
        pat = re.compile(r"(?<![\w.])%s\s*\(" % re.escape(name))
        pat_attr = re.compile(r"\.%s\s*\(" % re.escape(name))
        defpat = re.compile(r"\s*(async\s+)?def\s+%s\s*\(" % re.escape(name))
        out = []
        for r, src in scopes.src_lines.items():
            for idx, line in enumerate(src, 1):
                if defpat.match(line):
                    continue
                if pat.search(line) or pat_attr.search(line):
                    out.append({"file": r, "lineno": idx,
                                "executed": idx in union.get(r, set()),
                                "text": line.strip()})
        _ref_cache[key] = out
        return out

    empty_rules = [r for r in universe["rules"] if not cov.get(r["rule_id"])]
    results = []
    for rule in empty_rules:
        anchor = rule["anchor"]
        f, _, line = anchor.rpartition(":")
        line = int(line)
        scope = scopes.innermost(f, line)
        scope_key = scope["qualname"] if scope else "<module>"
        executed_lines = union.get(f, set())
        if scope:
            ran = [l for l in range(scope["lineno"], scope["end_lineno"] + 1)
                   if l in executed_lines]
        else:
            ran = sorted(executed_lines)
        file_lines = len(executed_lines)

        importers = importers_of(f)
        in_core = [i for i in importers if i["file"].startswith("core/")
                   and i["file"] != "core/cfg/__init__.py"]
        barrel = [i for i in importers if i["file"] == "core/cfg/__init__.py"]
        cli = [i for i in importers if not i["file"].startswith("core/")]
        refs = refs_of_symbol(scope["name"], f) if scope else []
        live_refs = [r for r in refs if r["executed"]]
        in_closure = module_of(f) in closure

        class_name = None
        class_span = None
        class_lines_executed = 0
        if scope and "." in scope["qualname"]:
            class_span = scopes.class_of(f, scope["qualname"])
            if class_span:
                class_name = class_span["name"]
                class_lines_executed = len(
                    [l for l in range(class_span["lineno"], class_span["end_lineno"] + 1)
                     if l in executed_lines])

        if file_lines == 0:
            tier = "D1"
            tier_kind = ("no_consumer_importer" if not in_core
                         else "consumer_importer_never_executes")
        elif ran:
            tier = "D3"
            tier_kind = "function_entered_branch_unhit"
        else:
            tier = "D2"
            if class_span and class_lines_executed:
                tier_kind = "class_live_callee_unentered"
            elif class_span:
                tier_kind = "class_never_constructed"
            else:
                tier_kind = "module_function_unentered"

        results.append({
            "rule_id": rule["rule_id"],
            "anchor": anchor,
            "file": f,
            "line": line,
            "kind": rule["kind"],
            "symbol": rule["symbol"],
            "pattern": rule.get("pattern"),
            "occurrences": rule.get("occurrences"),
            "anchors": rule.get("anchors") or [],
            "scope": scope_key,
            "scope_span": [scope["lineno"], scope["end_lineno"]] if scope else None,
            "scope_lines_executed": len(ran),
            "scope_lines_total": (scope["end_lineno"] - scope["lineno"] + 1) if scope else None,
            "file_lines_executed": file_lines,
            "tier": tier,
            "tier_kind": tier_kind,
            "class_name": class_name,
            "class_span": [class_span["lineno"], class_span["end_lineno"]] if class_span else None,
            "class_lines_executed": class_lines_executed,
            "in_pycdc_import_closure": in_closure,
            "closure_via": closure.get(module_of(f)),
            "importers": importers,
            "importers_in_core": in_core,
            "importers_barrel": barrel,
            "importers_cli": cli,
            "refs_total": len(refs),
            "refs_executed": len(live_refs),
            "refs_top": refs[:6],
        })

    by_tier = collections.Counter(r["tier"] for r in results)
    by_scope = collections.Counter((r["file"], r["scope"]) for r in results)
    payload = {
        "tool": "g4-unreachable-dossier",
        "version": "1.0.0",
        "note": ("Evidence only. No rule status/witness/domain/proof/composition is touched; "
                 "the universe is read, never rewritten."),
        "universe": os.path.abspath(args.universe).replace("\\", "/"),
        "coverage": os.path.abspath(args.coverage).replace("\\", "/"),
        "coverage_sha256": coverage.get("universe_sha256"),
        "exec_data": os.path.abspath(args.exec_path).replace("\\", "/"),
        "total_rules": universe["total_rules"],
        "empty_cov": len(results),
        "tiers": {t: by_tier.get(t, 0) for t in ("D1", "D2", "D3")},
        "tier_kinds": dict(collections.Counter(r["tier_kind"] for r in results)),
        "pycdc_seeds": seeds,
        "files_executed_lines": {k: len(v) for k, v in sorted(union.items())},
        "rules": results,
        "clusters": [{"file": f, "scope": s, "rules": n}
                     for (f, s), n in sorted(by_scope.items(), key=lambda kv: (-kv[1], kv[0]))],
    }
    with open(args.out_json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    if args.out_md:
        with open(args.out_md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_md(payload, universe, coverage, execdata))
    print("[dossier] empty_cov=%d tiers=%s kinds=%s"
          % (len(results), payload["tiers"], payload["tier_kinds"]))
    for (f, s), n in sorted(by_scope.items(), key=lambda kv: (-kv[1], kv[0])):
        sub = collections.Counter(r["tier"] for r in results
                                  if r["file"] == f and r["scope"] == s)
        print("[dossier]   %-38s %-52s %2d  %s" % (f.split("cfg/")[-1], s, n, dict(sub)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
