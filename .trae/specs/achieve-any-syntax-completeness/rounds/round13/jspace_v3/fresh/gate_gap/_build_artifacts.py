#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the G4 gap probe artefacts (read-only w.r.t. core/ and tools/).

Writes into ``fresh/gate_gap/``:
  probes_manifest.json   per-probe static facts (p_j / pyc / calls / labels)
  g4_probe_entries.json  incremental J-space entries (judgment_space schema)

Writes into ``D:\\temp\\opencode\\cl_layout\\gap\\`` (temporary merge, only):
  jspace_plus.json       judgment_space entries + g4_probe_entries entries

Usage:
  python -I -X utf8 _build_artifacts.py [--merge]
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = r"D:\temp\opencode\cl_layout\gap"
JSPACE = ".trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json"

# name -> (cluster index, cluster label, target rule ids, expected_label, entry id)
PLAN = {
    "pj_dictnode_01": (
        1, "code_generator::CodeGenerator._generate_dict_node",
        ["RULE-0b22204ea11f", "RULE-1601748f4b42", "RULE-1b5b4d7115d9",
         "RULE-1f2bf6bdcd1e", "RULE-3b46d229d0af", "RULE-3c8a43d55e71",
         "RULE-3ed21c936d06", "RULE-702b6dd6ca34", "RULE-8c816c79d0c7",
         "RULE-a99b10fa310d", "RULE-cc118c63f579", "RULE-d712e20d2506",
         "RULE-df8d199ebe90", "RULE-dff33ce626a7", "RULE-eb29ec1ad01a",
         "RULE-eed79a22277c"],
        {"form": "Global", "variant": "global-in-func", "host": "function-body",
         "depth": "d1 单层"},
        "PJ-DICTNODE-001"),
    "pj_dictnode_02": (
        1, "code_generator::CodeGenerator._generate_dict_node", [],
        {"form": "AnnAssign", "variant": "ann-in-func", "host": "function-body",
         "depth": "d1 单层"},
        "PJ-DICTNODE-002"),
    "pj_dictnode_03": (
        1, "code_generator::CodeGenerator._generate_dict_node", [],
        {"form": "Match", "variant": "pat-mapping", "host": "function-body",
         "depth": "d1 单层"},
        "PJ-DICTNODE-003"),
    "pj_v2if_01": (
        2, "ast_generator_v2::ASTGeneratorV2._generate_if_ast",
        ["RULE-05f8183d28bc", "RULE-5361acaaa053", "RULE-b611d12faec6",
         "RULE-bcde89ee3e2a", "RULE-beabfd586993", "RULE-c56bc072e6e4",
         "RULE-c7b3c96bb6c8", "RULE-d1e1d76ee83d", "RULE-dda45a0ced72",
         "RULE-f1bef410c01e"],
        {"form": "If", "variant": "if-elif-chain", "host": "nested-func-body",
         "depth": "d2 双层"},
        "PJ-V2IF-001"),
    "pj_v2if_02": (
        2, "ast_generator_v2::ASTGeneratorV2._generate_if_ast", [],
        {"form": "If", "variant": "if-elif-chain", "host": "class-body",
         "depth": "d2 双层"},
        "PJ-V2IF-002"),
    "pj_elif_01": (
        3, "ast_generator_v2::ASTGeneratorV2._generate_if_ast.extract_elif_chain",
        ["RULE-010c1b2cf1d7", "RULE-6048d12971c9", "RULE-681e794c6afb",
         "RULE-6ce83d58fb8b", "RULE-ae6695fa4fca", "RULE-cbb06f6eb54d"],
        {"form": "If", "variant": "if-elif-chain", "host": "function-body",
         "depth": "d1 单层"},
        "PJ-ELIF-001"),
    "pj_elif_02": (
        3, "ast_generator_v2::ASTGeneratorV2._generate_if_ast.extract_elif_chain", [],
        {"form": "If", "variant": "if-elif-chain", "host": "elif-arm",
         "depth": "d2 双层"},
        "PJ-ELIF-002"),
    "pj_with_01": (
        4, "structured_analyzer::StructuredAnalyzer._identify_with_structures",
        ["RULE-7f1501983cc4", "RULE-a2f801d5aefb", "RULE-c500ada1eadd",
         "RULE-c708889ddc61", "RULE-fac0e268c522"],
        {"form": "With", "variant": "with-multi-item", "host": "function-body",
         "depth": "d1 单层"},
        "PJ-WITH-001"),
    "pj_with_02": (
        4, "structured_analyzer::StructuredAnalyzer._identify_with_structures", [],
        {"form": "AsyncWith", "variant": "aw-multi-item", "host": "async-func-body",
         "depth": "d1 单层"},
        "PJ-WITH-002"),
    "pj_patchpat_01": (
        5, "objective_patch_detector::ObjectivePatchDetector._extract_test_pattern",
        ["RULE-20568d2871b4", "RULE-2b862ecf9a11", "RULE-526c2f9c8010",
         "RULE-93efbfe2473b"],
        {"form": "BoolOp", "variant": "boolop-mixed-and-or", "host": "if-arm",
         "depth": "d1 单层"},
        "PJ-PATCHPAT-001"),
    "pj_patchpat_02": (
        5, "objective_patch_detector::ObjectivePatchDetector._extract_test_pattern", [],
        {"form": "BoolOp", "variant": "boolop-compare-operand", "host": "if-arm",
         "depth": "d1 单层"},
        "PJ-PATCHPAT-002"),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def zero_arg_callables(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    names = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = node.args
        req = list(args.posonlyargs) + list(args.args)
        n_def = len(args.defaults)
        required = len(req) - n_def + len(args.kwonlyargs) - len(args.kw_defaults)
        if required <= 0:
            names.append(node.name)
    names.sort()
    return ["%s()" % n for n in names]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    merge = "--merge" in argv
    root = HERE
    while not os.path.isdir(os.path.join(root, "core", "cfg")):
        nxt = os.path.dirname(root)
        if nxt == root:
            raise SystemExit("repo root not found")
        root = nxt

    probes = []
    entries = []
    missing = []
    for name in sorted(PLAN):
        cid, cluster, rules, label, eid = PLAN[name]
        p_j = os.path.join(HERE, "probes", name + ".py")
        pyc = p_j + "c"
        rel_src = os.path.relpath(p_j, root).replace("\\", "/")
        rel_pyc = os.path.relpath(pyc, root).replace("\\", "/")
        if not (os.path.isfile(p_j) and os.path.isfile(pyc)):
            missing.append(name)
            continue
        calls = zero_arg_callables(p_j)
        if not calls:
            raise SystemExit("probe %s has no zero-arg callable" % name)
        payload = {
            "id": eid,
            "form": label["form"],
            "host": label["host"],
            "depth": label["depth"],
            "variant": label["variant"],
            "row": label["form"],
            "required_evidence": [{"kind": "probe", "pyc": rel_pyc,
                                   "note": "round13 gate_gap reachability probe"}],
            "status": "uncovered",
            "source": "fresh/gate_gap/probes_manifest.json",
            "j_schema_version": "v2",
            "expected_label": dict(label),
            "counterexample_hint": None,
            "host_prelude": None,
            "excluded": [],
            "p_j": rel_src,
            "p_j_sha256": sha256(p_j),
            "p_j_lines": len(open(p_j, encoding="utf-8").read().splitlines()),
            "pyc": rel_pyc,
            "pyc_sha256": sha256(pyc),
            "pyc_present": True,
            "pyc_loadable": True,
            "input_model": {
                "kind": "module",
                "calls": calls,
                "seed": 0,
                "note": "zero-arg/defaulted callables derived from p_j source",
            },
            "entrypoint": "module",
            "host_prelude_reason": "host prelude is not derived from the probe source in J v2",
            "gate_gap": {
                "cluster": cid,
                "cluster_label": cluster,
                "target_rule_ids": rules,
                "purpose": "rule_anchor_reachability",
            },
        }
        entries.append(payload)
        probes.append({
            "id": eid,
            "probe": os.path.basename(p_j),
            "p_j": rel_src,
            "pyc": rel_pyc,
            "p_j_sha256": payload["p_j_sha256"],
            "pyc_sha256": payload["pyc_sha256"],
            "p_j_lines": payload["p_j_lines"],
            "input_model": payload["input_model"],
            "expected_label": label,
            "excluded": [],
            "status": "uncovered",
            "cluster": cid,
            "cluster_label": cluster,
            "target_rule_ids": rules,
        })

    clusters = {}
    for name in sorted(PLAN):
        cid, cluster, rules, _, _ = PLAN[name]
        slot = clusters.setdefault(str(cid), {"cluster": cid, "label": cluster,
                                              "target_rule_ids": rules,
                                              "probes": []})
        slot["probes"].append(PLAN[name][4])

    manifest = {
        "tool": "g4_probe_manifest",
        "version": "1.0.0",
        "note": ("Minimal new J probes aimed at the five largest G4 empty-coverage "
                 "clusters.  No status / witness / domain / proof is claimed here: "
                 "status stays 'uncovered'."),
        "jspace_base": JSPACE,
        "probes": probes,
        "clusters": [clusters[k] for k in sorted(clusters, key=int)],
        "counts": {
            "probes": len(probes),
            "target_rules": len({r for p in probes for r in p["target_rule_ids"]}),
            "clusters": len(clusters),
        },
        "missing": missing,
    }
    with open(os.path.join(HERE, "probes_manifest.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    bundle = {
        "tool": "g4_probe_entries",
        "version": "1.0.0",
        "note": ("Incremental J-space entries (judgment_space entry schema) for the "
                 "gate_gap probes.  Merge-only artefact: the authoritative J space "
                 "files are never modified."),
        "base_jspace": JSPACE,
        "entries": entries,
        "counts": {"entries": len(entries)},
    }
    with open(os.path.join(HERE, "g4_probe_entries.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(bundle, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    if merge:
        base = json.load(open(os.path.join(root, JSPACE), encoding="utf-8-sig"))
        merged = dict(base)
        merged["entries"] = list(base.get("entries") or []) + entries
        merged["gate_gap_probe_note"] = (
            "temporary merge for G4 re-trace: %d authoritative entries + %d gate_gap "
            "probe entries" % (len(base.get("entries") or []), len(entries)))
        os.makedirs(TMP, exist_ok=True)
        out = os.path.join(TMP, "jspace_plus.json")
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(merged, fh, ensure_ascii=False)
            fh.write("\n")
        print("[build] merged %s entries=%d (+%d)"
              % (out, len(merged["entries"]), len(entries)))
    print("[build] probes=%d entries=%d missing=%s"
          % (len(probes), len(entries), missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
