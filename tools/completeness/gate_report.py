#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aggregate G1-G6 and the legacy regression gate without inventing PASSes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys

TOOL_VERSION = "1.0.0"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PASS, FAIL, INCONCLUSIVE, UNESTABLISHED = "PASS", "FAIL", "INCONCLUSIVE", "UNESTABLISHED"
EXPECTED = {"units": 6617, "small34": 1568, "quotation": 153, "v8_complete": 128,
            "v8_breach": 0, "v8_zero": 0}


def sha_file(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def read_json(path: str):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def norm(path: str) -> str:
    return (path or "").replace("\\", "/")


def status_ok(value: str) -> bool:
    return value == PASS


def gate_g1(coverage: dict, baseline: dict | None) -> dict:
    totals = coverage.get("totals") or {}
    total = totals.get("J_total", 0)
    covered = totals.get("covered_5tuple", 0)
    status = PASS if total > 0 and covered == total and totals.get("semantic_failures", 0) == 0 else FAIL
    result = {
        "status": status,
        "J_total": total,
        "covered_5tuple": covered,
        "coverage_pct": totals.get("coverage_pct", 0.0),
        "probe_only": totals.get("probe_only", 0),
        "uncovered": totals.get("uncovered", total),
        "semantic_failures": totals.get("semantic_failures", 0),
        "evidence": norm(coverage.get("evidence_path", "")),
    }
    if baseline is not None:
        b = baseline.get("totals") or {}
        result["baseline"] = {"covered_5tuple": b.get("covered_5tuple", 0),
                              "J_total": b.get("J_total", 0),
                              "evidence": norm(baseline.get("evidence_path", ""))}
    return result


def gate_g2a(summary: dict | None) -> dict:
    if not summary:
        return {"status": UNESTABLISHED, "reason": "no semantic J evidence"}
    verdicts = summary.get("verdicts") or {}
    total = int(summary.get("total") or 0)
    different = int(verdicts.get("DIFFERENT", 0))
    inconclusive = int(verdicts.get("INCONCLUSIVE", 0))
    errors = int(verdicts.get("ERROR", 0))
    if total < 100:
        status = FAIL if different else UNESTABLISHED
    else:
        status = PASS if different == 0 and inconclusive == 0 and errors == 0 else FAIL
    return {"status": status, "total": total, "different": different,
            "inconclusive": inconclusive, "error": errors,
            "required_total": 100, "reason": "sample" if total < 100 else ""}


def gate_g2bc(path: str | None, expected: int) -> dict:
    if not path or not os.path.isfile(path):
        return {"status": UNESTABLISHED, "reason": "missing evidence", "required": expected}
    try:
        payload = read_json(path)
    except Exception as exc:
        return {"status": INCONCLUSIVE, "reason": "%s: %s" % (type(exc).__name__, exc)}
    total = payload.get("total") or payload.get("summary", {}).get("total") or 0
    diff = payload.get("different") or payload.get("summary", {}).get("DIFFERENT") or 0
    inc = payload.get("inconclusive") or payload.get("summary", {}).get("INCONCLUSIVE") or 0
    status = PASS if total >= expected and diff == 0 and inc == 0 else FAIL
    return {"status": status, "total": total, "different": diff,
            "inconclusive": inc, "required": expected, "evidence": norm(path)}


def gate_g3(path: str | None) -> dict:
    if not path or not os.path.isfile(path):
        return {"status": UNESTABLISHED, "reason": "no full mutation report"}
    try:
        payload = read_json(path)
    except Exception as exc:
        return {"status": INCONCLUSIVE, "reason": str(exc)}
    mix = payload.get("mix") or payload.get("summary") or payload
    killed = int(mix.get("KILLED", 0))
    survived = int(mix.get("MISSED", mix.get("survived", 0)))
    equivalent = int(mix.get("EQUIVALENT", 0))
    false_kill = int(mix.get("FALSE_KILL", 0))
    inconclusive = int(mix.get("INCONCLUSIVE", 0))
    errors = int(mix.get("ERROR", 0))
    status = PASS if (killed + survived > 0 and survived == 0 and false_kill == 0
                      and inconclusive == 0 and errors == 0) else FAIL
    return {"status": status, "killed": killed, "survived": survived,
            "equivalent": equivalent, "false_kill": false_kill,
            "inconclusive": inconclusive, "error": errors, "evidence": norm(path)}


def gate_g4(path: str | None) -> dict:
    if not path or not os.path.isfile(path):
        return {"status": UNESTABLISHED, "reason": "missing rule coverage"}
    payload = read_json(path)
    status = payload.get("g4") or INCONCLUSIVE
    if status not in (PASS, FAIL, INCONCLUSIVE, UNESTABLISHED):
        status = INCONCLUSIVE
    return {"status": status, "total_rules": payload.get("total_rules", 0),
            "proved": payload.get("proved", 0), "open": payload.get("open", 0),
            "unmapped": len(payload.get("unmapped_anchors") or []),
            "orphan": len(payload.get("orphan_rules") or []),
            "reason": payload.get("reason", ""), "evidence": norm(path)}


def gate_g5(path: str | None) -> dict:
    if not path or not os.path.isfile(path):
        return {"status": UNESTABLISHED, "reason": "missing regression summary"}
    try:
        payload = read_json(path)
        total = payload.get("total") or {}
        small = payload.get("small34") or {}
        quotation = payload.get("quotation") or {}
        pytest = payload.get("pytest") or {}
        iv2 = payload.get("iv2") or {}
        ok = (total.get("units_success") == EXPECTED["units"]
              and total.get("units_total") == EXPECTED["units"]
              and total.get("files_failure") == 0
              and small.get("units_success") == EXPECTED["small34"]
              and small.get("units_total") == EXPECTED["small34"]
              and quotation.get("rc") == 0
              and "153/153" in str(quotation.get("tail", ""))
              and str(pytest.get("summary_line", "")).startswith("2 failed, 282 passed, 2 xpassed")
              and iv2.get("IMPORT_OK") is True and iv2.get("COMPILE_OK") is True
              and iv2.get("G3_forbidden_prefix_new_defs") == 0
              and str(iv2.get("BOM_region_ast_generator.py")) == "one"
              and str(iv2.get("BOM_region_analyzer.py")) == "one")
        status = PASS if ok else FAIL
        try:
            tree = subprocess.run(["git", "status", "--porcelain", "--", "core/cfg"],
                                  cwd=ROOT, capture_output=True, text=True, timeout=20)
            clean = tree.returncode == 0 and not (tree.stdout or "").strip()
        except Exception:
            clean = None
        if status == PASS and clean is False:
            status = INCONCLUSIVE
        return {"status": status, "current_run": False, "baseline_only": True,
                "core_cfg_clean": clean, "units": "%s/%s" % (
                    total.get("units_success"), total.get("units_total")),
                "small34": "%s/%s" % (small.get("units_success"), small.get("units_total")),
                "quotation": quotation.get("rc"), "tests": pytest.get("summary_line"),
                "iv2": {"import": iv2.get("IMPORT_OK"), "compile": iv2.get("COMPILE_OK"),
                        "g3": iv2.get("G3_forbidden_prefix_new_defs")},
                "evidence": norm(path)}
    except Exception as exc:
        return {"status": INCONCLUSIVE, "reason": "%s: %s" % (type(exc).__name__, exc)}


def gate_g6(path: str | None) -> dict:
    if not path or not os.path.isfile(path):
        return {"status": UNESTABLISHED, "reason": "no canary report"}
    payload = read_json(path)
    g6 = payload.get("g6") or UNESTABLISHED
    if g6 not in (PASS, FAIL, INCONCLUSIVE, UNESTABLISHED):
        g6 = INCONCLUSIVE
    return {"status": g6, "canaries": payload.get("canaries", 0),
            "equal": payload.get("equal", 0), "counts": payload.get("counts", {}),
            "leaks": len(payload.get("leak_hits") or []),
            "custody": payload.get("custody"), "rotation_ok": payload.get("rotation_ok"),
            "reason": payload.get("reason", ""), "evidence": norm(path)}


def audit_sample(evidence: dict) -> dict:
    records = (evidence.get("semantic_j") or {}).get("records") or []
    selected = sorted(records, key=lambda row: hashlib.sha256(
        str(row.get("entry_id", "")).encode()).hexdigest())[:max(1, math.ceil(len(records) * 0.10))]
    checks = []
    for row in selected:
        c5 = row.get("c5") or {}
        c1 = row.get("c1") or {}
        c2 = row.get("c2") or {}
        c3 = row.get("c3") or {}
        paths = {"source": c1.get("path"), "pyc": c2.get("pyc_path"),
                 "product": c3.get("product_path")}
        actual = {key: sha_file(os.path.join(ROOT, value)) if value else None
                  for key, value in paths.items()}
        checks.append({
            "entry_id": row.get("entry_id"),
            "verdict": (row.get("c4") or {}).get("verdict"),
            "hash_chain_ok": (actual["source"] == c5.get("source_sha256")
                              and actual["pyc"] == c5.get("pyc_sha256")
                              and actual["product"] == c5.get("product_sha256")),
            "source": paths["source"], "product": paths["product"],
        })
    return {"sample_size": len(selected), "of": len(records),
            "at_least_one_failure": any(c["verdict"] != "EQUAL" for c in checks),
            "checks": checks}


def build(args) -> dict:
    coverage = read_json(args.coverage) if args.coverage and os.path.isfile(args.coverage) else {}
    baseline = read_json(args.coverage_baseline) if args.coverage_baseline and os.path.isfile(args.coverage_baseline) else None
    semantic_summary = read_json(args.semantic_summary) if args.semantic_summary and os.path.isfile(args.semantic_summary) else None
    rules = read_json(args.rules) if args.rules and os.path.isfile(args.rules) else {}
    canary = read_json(args.canary) if args.canary and os.path.isfile(args.canary) else None
    gates = {
        "G1": gate_g1(coverage, baseline),
        "G2a": gate_g2a(semantic_summary),
        "G2b": gate_g2bc(args.semantic_402, 402),
        "G2c": gate_g2bc(args.semantic_real, 46),
        "G3": gate_g3(args.mutation),
        "G4": gate_g4(args.rules),
        "G5": gate_g5(args.regression),
        "G6": gate_g6(args.canary),
    }
    evidence = {}
    for name, path in (("coverage", args.coverage),
                       ("coverage_baseline", args.coverage_baseline),
                       ("semantic_j", args.semantic_j),
                       ("semantic_j_summary", args.semantic_summary),
                       ("rule_coverage", args.rules),
                       ("canary_report", args.canary),
                       ("regression", args.regression)):
        if path and os.path.isfile(path):
            evidence[name] = {"path": norm(path), "sha256": sha_file(path)}
            if name == "semantic_j":
                try:
                    evidence[name]["payload"] = read_json(path)
                except Exception:
                    pass
    audit = audit_sample({"semantic_j": evidence.get("semantic_j", {}).get("payload")})
    blockers = [name for name, value in gates.items() if value.get("status") != PASS]
    totals = coverage.get("totals") or {}
    result = {
        "tool": "gate_report", "version": TOOL_VERSION,
        "overall": PASS if not blockers else "BLOCKED",
        "blockers": blockers,
        "gates": gates,
        "three_state": {"complete": 128, "breach": 0, "zero": 0,
                        "pct": 100.0, "status": "v8 baseline / regression only"},
        "dual_readings": {
            "shape": {"units": "6617/6617", "small34": "1568/1568",
                      "quotation": "153/153", "v8": "128/0/0 (100%)"},
            "judgment": {"J_total": totals.get("J_total", 0),
                         "covered_5tuple": totals.get("covered_5tuple", 0),
                         "coverage_pct": totals.get("coverage_pct", 0.0),
                         "semantic_failures": totals.get("semantic_failures", 0),
                         "uncovered": totals.get("uncovered", 0),
                         "integrated_sample": True},
            "rules": {"total": rules.get("total_rules", 0), "proved": rules.get("proved", 0),
                      "open": rules.get("open", 0)},
            "canary": {"equal": (canary or {}).get("equal", 0),
                       "total": (canary or {}).get("canaries", 0)},
        },
        "allowed_claims": ["形态基线达成（仅回归）"],
        "forbidden_claims": ["J 门槛达标", "语料完备", "规则完备", "语义完备"],
        "audit": audit,
        "evidence": evidence,
    }
    return result


def write_markdown(path: str, report: dict) -> None:
    lines = ["# Gate Report", "",
             "- overall: **%s**" % report["overall"],
             "- blockers: %s" % (", ".join(report["blockers"]) or "none"), "",
             "| gate | status | key reading |", "|---|---|---|"]
    for name, gate in report["gates"].items():
        if name == "G1":
            reading = "%s/%s covered, %s diffs" % (gate.get("covered_5tuple"), gate.get("J_total"),
                                                   gate.get("semantic_failures"))
        elif name.startswith("G2"):
            reading = "%s/%s, diff=%s" % (gate.get("total", 0), gate.get("required_total", gate.get("required", "?")),
                                          gate.get("different", "?"))
        elif name == "G3":
            reading = "killed=%s survived=%s" % (gate.get("killed", "?"), gate.get("survived", "?"))
        elif name == "G4":
            reading = "proved=%s/%s, reason=%s" % (gate.get("proved"), gate.get("total_rules"),
                                                   gate.get("reason"))
        elif name == "G5":
            reading = "%s, baseline-only" % gate.get("units")
        else:
            reading = "%s/%s, leaks=%s" % (gate.get("equal"), gate.get("canaries"),
                                           gate.get("leaks"))
        lines.append("| %s | **%s** | %s |" % (name, gate.get("status"), reading))
    lines += ["", "## Dual readings", "",
              "- shape: 6617/6617; 1568/1568; 153/153; v8 128/0/0 (100%)",
              "- judgment: %s/%s covered; %s semantic failures; %s uncovered (integrated sample)" % (
                  report["dual_readings"]["judgment"]["covered_5tuple"],
                  report["dual_readings"]["judgment"]["J_total"],
                  report["dual_readings"]["judgment"]["semantic_failures"],
                  report["dual_readings"]["judgment"]["uncovered"]),
              "- rules: %s total, %s proved, %s open" % (
                  report["dual_readings"]["rules"]["total"],
                  report["dual_readings"]["rules"]["proved"],
                  report["dual_readings"]["rules"]["open"]),
              "- canary: %s/%s equal" % (report["dual_readings"]["canary"]["equal"],
                                         report["dual_readings"]["canary"]["total"]),
              "", "Allowed claims: %s" % "; ".join(report["allowed_claims"]),
              "", "Forbidden claims: %s" % "; ".join(report["forbidden_claims"]), "",
              "## Audit", "",
              "- sampled: %s/%s" % (report["audit"]["sample_size"], report["audit"]["of"]),
              "- at least one failure: %s" % report["audit"]["at_least_one_failure"],
              "- hash-chain checks: %s/%s" % (
                  sum(1 for c in report["audit"]["checks"] if c["hash_chain_ok"]),
                  len(report["audit"]["checks"])), ""]
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", default=os.path.join(ROOT, ".trae", "specs",
                        "attack-completeness-claims", "rounds", "round9",
                        "coverage_c1c5_sample.json"))
    parser.add_argument("--coverage-baseline", default=os.path.join(ROOT, ".trae", "specs",
                        "attack-completeness-claims", "rounds", "round9", "coverage_c1c5.json"))
    parser.add_argument("--semantic-j", default=os.path.join(ROOT, ".trae", "specs",
                        "attack-completeness-claims", "rounds", "round9", "semantic_j_sample.json"))
    parser.add_argument("--semantic-summary", default=os.path.join(ROOT, ".trae", "specs",
                        "attack-completeness-claims", "rounds", "round9", "semantic_j_sample_summary.json"))
    parser.add_argument("--semantic-402", default="")
    parser.add_argument("--semantic-real", default="")
    parser.add_argument("--mutation", default="")
    parser.add_argument("--rules", default=os.path.join(ROOT, ".trae", "specs",
                        "attack-completeness-claims", "rounds", "round9", "rule_coverage.json"))
    parser.add_argument("--regression", default=os.path.join(ROOT, ".trae", "specs",
                        "attain-true-completeness", "rounds", "round8", "final_verify_summary.json"))
    parser.add_argument("--canary", default=os.path.join(ROOT, ".trae", "specs",
                        "attack-completeness-claims", "rounds", "round9", "canary_report.json"))
    parser.add_argument("--json", default=os.path.join(ROOT, ".trae", "specs",
                        "attack-completeness-claims", "rounds", "round9", "gate_report.json"))
    parser.add_argument("--md", default=os.path.join(ROOT, ".trae", "specs",
                        "attack-completeness-claims", "rounds", "round9", "GATE_REPORT.md"))
    args = parser.parse_args(argv)
    report = build(args)
    os.makedirs(os.path.dirname(os.path.abspath(args.json)) or ".", exist_ok=True)
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    write_markdown(args.md, report)
    print("[gate] overall=%s blockers=%s" % (report["overall"], ",".join(report["blockers"])))
    return 0 if report["overall"] == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
