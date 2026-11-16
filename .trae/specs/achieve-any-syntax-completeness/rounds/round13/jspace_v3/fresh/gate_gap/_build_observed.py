#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collect the measured G4 probe readings into fresh/gate_gap/g4_probe_observed.json."""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = HERE
TMP = r"D:\temp\opencode\cl_layout\gap"
AUD = os.path.join(os.path.dirname(GAP), "g4_audit")


def load(p):
    with open(p, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def main():
    empty = load(os.path.join(GAP, "g4_empty_cov.json"))
    manifest = load(os.path.join(GAP, "probes_manifest.json"))
    entries = load(os.path.join(GAP, "g4_probe_entries.json"))["entries"]

    old = load(os.path.join(AUD, "rule_traces_current.json"))
    base = load(os.path.join(TMP, "rule_traces_base_today.json"))
    plus = load(os.path.join(TMP, "rule_traces_plus.json"))
    cov_base = load(os.path.join(TMP, "rule_coverage_base_today.json"))
    cov_plus = load(os.path.join(TMP, "rule_coverage_plus.json"))

    old_hit = set()
    for rec in old["records"]:
        old_hit.update(rec["rule_ids"])
    base_hit = {rid for rid, v in cov_base["coverage"].items() if v}
    plus_hit = {rid for rid, v in cov_plus["coverage"].items() if v}

    targets = []
    for cluster in empty["clusters"][:5]:
        for rid in cluster["empty_rule_ids"]:
            targets.append((cluster["cluster"], rid))
    rule_set = {rid for _, rid in targets}

    per_probe = {}
    for rec in plus["records"]:
        if not rec["entry_id"].startswith("PJ-"):
            continue
        per_probe[rec["entry_id"]] = {
            "rule_ids_total": len(rec["rule_ids"]),
            "target_rule_hits": sorted(rule_set & set(rec["rule_ids"])),
        }

    per_cluster = []
    for cluster in empty["clusters"][:5]:
        rids = cluster["empty_rule_ids"]
        per_cluster.append({
            "cluster": cluster["cluster"],
            "rules": len(rids),
            "hit_by_probes": sum(1 for r in rids if r in plus_hit),
            "still_empty_today": sum(1 for r in rids if r not in plus_hit),
        })

    payload = {
        "tool": "g4_probe_observed",
        "version": "1.0.0",
        "note": ("Measured readings of the gate_gap probe round.  This file records "
                 "coverage/hit observations only: no rule status, witness, domain or "
                 "proof is written."),
        "runs": {
            "oct27_traces": {
                "path": os.path.join(AUD, "rule_traces_current.json").replace("\\", "/"),
                "entries": len(old["records"]),
                "failed": old["summary"]["failed_entries"],
                "rules_hit": len(old_hit),
                "empty_cov": 342 - len(old_hit),
                "note": "authoritative baseline used by g4_empty_cov.json (2026-10-27)",
            },
            "today_baseline": {
                "path": os.path.join(TMP, "rule_traces_base_today.json").replace("\\", "/"),
                "entries": len(base["records"]),
                "failed": base["summary"]["failed_entries"],
                "rules_hit": len(base_hit),
                "empty_cov": cov_base["empty_cov"],
                "g4": cov_base["g4"],
                "note": "same 1556 J entries re-traced on the current core/ tree",
            },
            "today_with_probes": {
                "path": os.path.join(TMP, "rule_traces_plus.json").replace("\\", "/"),
                "entries": len(plus["records"]),
                "failed": plus["summary"]["failed_entries"],
                "rules_hit": len(plus_hit),
                "empty_cov": cov_plus["empty_cov"],
                "g4": cov_plus["g4"],
                "note": "1556 J entries + 11 gate_gap probe entries, current core/ tree",
            },
        },
        "deltas": {
            "oct27_to_today_baseline": len(base_hit) - len(old_hit),
            "probes_vs_today_baseline": len(plus_hit) - len(base_hit),
            "lost_since_oct27": sorted(old_hit - base_hit),
            "gained_since_oct27": sorted(base_hit - old_hit),
        },
        "target_clusters": per_cluster,
        "probes": {
            "count": len(entries),
            "trace_results": per_probe,
            "target_rule_hits_total": len(rule_set & plus_hit),
            "target_rules_total": len(rule_set),
        },
        "rule_status_written": False,
        "witness_written": False,
        "proof_written": False,
    }
    out = os.path.join(GAP, "g4_probe_observed.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("[observed] %s" % out)
    print("[observed] empty_cov oct27=%d today=%d plus=%d target_hits=%d/%d"
          % (payload["runs"]["oct27_traces"]["empty_cov"],
             payload["runs"]["today_baseline"]["empty_cov"],
             payload["runs"]["today_with_probes"]["empty_cov"],
             payload["probes"]["target_rule_hits_total"],
             payload["probes"]["target_rules_total"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
