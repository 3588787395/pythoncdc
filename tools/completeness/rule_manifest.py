#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rule manifest mapping and G4 reconciliation (Task 9.4).

The denominator is the independent rule_universe.json, never this manifest.
The manifest only maps every universe rule to proof obligations and witnesses.

CLI:
    python -X utf8 tools/completeness/rule_manifest.py --generate \
        --universe logs/rule_universe.json --manifest tools/completeness/rule_manifest.json
    python -X utf8 tools/completeness/rule_manifest.py --check \
        --universe logs/rule_universe.json --manifest tools/completeness/rule_manifest.json \
        --jspace judgment_space.json --traces rule_traces.json --json logs/rule_coverage.json
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sys

TOOL_VERSION = "1.0.0"
STATUSES = ("proved", "tested-only", "open")


def canonical(data) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(data) -> str:
    return hashlib.sha256(canonical(data).encode("utf-8")).hexdigest()


def load(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def _anchors(rule):
    out = list(rule.get("anchors") or [])
    if rule.get("anchor"):
        out.append(rule["anchor"])
    return list(dict.fromkeys(out))


def generate(universe):
    rules = []
    for item in universe.get("rules") or []:
        rules.append({
            "rule_id": item["rule_id"],
            "universe_id": item["rule_id"],
            "anchor": item["anchor"],
            "anchors": _anchors(item),
            "pattern": item.get("pattern"),
            "patterns": item.get("patterns") or [item.get("pattern")],
            "preconditions": [],
            "effect": "unclassified",
            "guards": [],
            "invariants": [],
            "semantic_domain": {"hosts": [], "depths": [], "note": "not declared in v1"},
            "witnesses": {"positive": [], "negative": []},
            "composition": [],
            "proof": {"proof_id": None, "checker_version": TOOL_VERSION,
                      "counterexample_bound": None, "review": None},
            "status": "open",
        })
    return {
        "tool": "rule_manifest", "version": TOOL_VERSION,
        "universe_sha256": digest(universe),
        "source": "rule_universe.json",
        "total_rules": len(rules),
        "rules": rules,
    }


def _trace_map(traces):
    if traces is None:
        return None
    out = collections.defaultdict(list)
    if isinstance(traces, dict):
        if "records" in traces and isinstance(traces["records"], list):
            records = traces["records"]
            for item in records:
                if isinstance(item, dict):
                    eid = item.get("entry_id") or item.get("id")
                    if eid:
                        out[eid].extend(item.get("rule_ids") or item.get("rules") or [])
        else:
            for key, value in traces.items():
                if isinstance(value, list):
                    out[key].extend(value)
                elif isinstance(value, dict):
                    out[key].extend(value.get("rule_ids") or value.get("rules") or [])
    elif isinstance(traces, list):
        for item in traces:
            if isinstance(item, dict):
                eid = item.get("entry_id") or item.get("id")
                if eid:
                    out[eid].extend(item.get("rule_ids") or item.get("rules") or [])
    return dict(out)


def _witness_ok(rule, jids):
    witnesses = rule.get("witnesses") or {}
    positive = witnesses.get("positive") or []
    negative = witnesses.get("negative") or []
    if not positive or not negative:
        return False, "witness_missing"
    if jids is not None:
        missing = [x for x in positive + negative if x not in jids]
        if missing:
            return False, "witness_not_in_J"
    return True, "ok"


def _domain_ok(rule):
    domain = rule.get("semantic_domain") or {}
    if rule.get("status") != "proved":
        return True, "not_proved"
    if not (domain.get("hosts") and domain.get("depths")):
        return False, "domain_missing"
    return True, "ok"


def check(universe, manifest, jspace=None, traces=None):
    universe_rules = universe.get("rules") or []
    manifest_rules = manifest.get("rules") or []
    umap = {}
    for item in universe_rules:
        umap[item.get("rule_id")] = item
    mmap = {}
    for item in manifest_rules:
        key = item.get("universe_id") or item.get("rule_id")
        mmap[key] = item
    unmapped = [item.get("rule_id") for item in universe_rules
                if not item.get("rule_id") in mmap]
    orphan = [item.get("rule_id") for item in manifest_rules
              if (item.get("universe_id") or item.get("rule_id")) not in umap]
    anchor_orphans = []
    for item in manifest_rules:
        if (item.get("universe_id") or item.get("rule_id")) in umap:
            continue
        for anchor in _anchors(item):
            if any(anchor in _anchors(u) for u in universe_rules):
                anchor_orphans.append(item.get("rule_id"))
                break
    jids = None
    if jspace is not None:
        jids = {e.get("id") for e in (jspace.get("entries") or []) if isinstance(e, dict)}
    statuses = collections.Counter(item.get("status") for item in manifest_rules)
    ready = not_ready = 0
    witness_errors = []
    domain_errors = []
    for rid, item in mmap.items():
        if rid not in umap:
            continue
        w_ok, w_reason = _witness_ok(item, jids)
        d_ok, d_reason = _domain_ok(item)
        proof = item.get("proof") or {}
        proof_ok = bool(proof.get("proof_id"))
        composition_ok = bool(item.get("composition"))
        if item.get("status") == "proved" and (not w_ok or not d_ok or not proof_ok or not composition_ok):
            not_ready += 1
            if not w_ok:
                witness_errors.append({"rule_id": rid, "reason": w_reason})
            if not d_ok:
                domain_errors.append({"rule_id": rid, "reason": d_reason})
        elif item.get("status") == "proved":
            ready += 1
    trace_map = _trace_map(traces)
    coverage_evaluable = trace_map is not None
    empty_cov = None
    coverage = {}
    if coverage_evaluable:
        for item in universe_rules:
            rid = item.get("rule_id")
            cov = sorted(eid for eid, rule_ids in trace_map.items() if rid in rule_ids)
            coverage[rid] = cov
        empty_cov = sum(1 for rid, cov in coverage.items() if not cov)
    total = len(universe_rules)
    if total == 0:
        g4 = "INCONCLUSIVE"
        reason = "empty_universe"
    elif not coverage_evaluable:
        g4 = "INCONCLUSIVE"
        reason = "no_rule_traces"
    elif unmapped or orphan or anchor_orphans or not_ready or empty_cov:
        g4 = "FAIL"
        reason = "mapping_or_proof_gap"
    elif ready != total:
        g4 = "FAIL"
        reason = "not_all_proved"
    else:
        g4 = "PASS"
        reason = "ok"
    return {
        "tool": "rule_manifest", "version": TOOL_VERSION,
        "universe_sha256": digest(universe),
        "manifest_sha256": digest(manifest),
        "total_rules": total,
        "manifest_rules": len(manifest_rules),
        "unmapped_anchors": unmapped,
        "orphan_rules": orphan,
        "anchor_orphans": anchor_orphans,
        "proved": statuses.get("proved", 0),
        "tested_only": statuses.get("tested-only", 0),
        "open": statuses.get("open", 0),
        "ready_proved": ready,
        "not_ready_proved": not_ready,
        "witness_errors": witness_errors,
        "domain_errors": domain_errors,
        "coverage_evaluable": coverage_evaluable,
        "empty_cov": empty_cov,
        "coverage": coverage,
        "g4": g4,
        "reason": reason,
    }


def write_json(path, data):
    if not path:
        return
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="rule manifest and G4 reconciliation")
    parser.add_argument("--universe", required=True)
    parser.add_argument("--manifest", default="tools/completeness/rule_manifest.json")
    parser.add_argument("--jspace", default="")
    parser.add_argument("--traces", default="")
    parser.add_argument("--json", default="")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    args = parser.parse_args(argv)
    universe = load(args.universe)
    if args.generate:
        manifest = generate(universe)
        write_json(args.manifest, manifest)
        print("[rule_manifest] generated %s rules=%d" % (args.manifest, manifest["total_rules"]))
        return 0
    if not args.check:
        parser.error("use --generate or --check")
    manifest = load(args.manifest)
    jspace = load(args.jspace) if args.jspace else None
    traces = load(args.traces) if args.traces else None
    result = check(universe, manifest, jspace, traces)
    write_json(args.json, result)
    print("[rule_manifest] total_rules=%d manifest=%d unmapped=%d orphan=%d proved=%d "
          "tested_only=%d open=%d empty_cov=%s G4=%s reason=%s"
          % (result["total_rules"], result["manifest_rules"], len(result["unmapped_anchors"]),
             len(result["orphan_rules"]), result["proved"], result["tested_only"],
             result["open"], result["empty_cov"], result["g4"], result["reason"]))
    if result["g4"] == "INCONCLUSIVE":
        return 2
    return 0 if result["g4"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
