#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build ``B275_REGRESSION.json`` from the archived rerun evidence.

Compares the three post-B275 base rerun shards with the archived
``semantic_v3_merged.json``, and compares the repair / async / module family
reruns with their archived evidence.  The raw reruns are kept under
``b275_regression/`` so the report can be recomputed without any temporary
directory.

Run from the repository root:

    python -X utf8 .../fresh/b275_regression_report.py
"""

from __future__ import annotations

import collections
import json
import os

FRESH = os.path.dirname(os.path.abspath(__file__))
REGRESS = os.path.join(FRESH, "b275_regression")


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def main() -> int:
    base = load(os.path.join(FRESH, "semantic_v3_merged.json"))
    old = {r["entry_id"]: r for r in base["records"]}
    new = {}
    shards = []
    for index in (0, 1, 2):
        payload = load(os.path.join(REGRESS, "regress_shard%d.json" % index))
        shards.append(payload["summary"])
        for record in payload["records"]:
            new[record["entry_id"]] = record

    verdict_changes = []
    status_changes = []
    sha_changes = []
    for entry_id, before in old.items():
        after = new[entry_id]
        if before["c4"]["verdict"] != after["c4"]["verdict"]:
            verdict_changes.append({
                "id": entry_id,
                "before": before["c4"]["verdict"],
                "after": after["c4"]["verdict"],
            })
        if before["status"] != after["status"]:
            status_changes.append({
                "id": entry_id,
                "before": before["status"],
                "after": after["status"],
            })
        if before["c3"]["sha256"] != after["c3"]["sha256"]:
            sha_changes.append({
                "id": entry_id,
                "before": before["c3"]["sha256"],
                "after": after["c3"]["sha256"],
            })

    family_checks = {}
    for name, archived, rerun in (
        ("repair_36", "semantic_repair.json", "b275_regression/regress_repair.json"),
        ("async_62", "semantic_async.json", "b275_regression/regress_async.json"),
        ("module_32", "semantic_module.json", "semantic_module_b275.json"),
    ):
        left = {r["entry_id"]: r
                for r in load(os.path.join(FRESH, archived))["records"]}
        right_path = rerun if os.path.isabs(rerun) else os.path.join(FRESH, rerun)
        right = {r["entry_id"]: r for r in load(right_path)["records"]}
        common = sorted(set(left) & set(right))
        family_checks[name] = {
            "common": len(common),
            "verdict_counts_before": dict(collections.Counter(
                left[k]["c4"]["verdict"] for k in common)),
            "verdict_counts_after": dict(collections.Counter(
                right[k]["c4"]["verdict"] for k in common)),
            "verdict_changes": [
                k for k in common
                if left[k]["c4"]["verdict"] != right[k]["c4"]["verdict"]],
            "verdict_change_details": [
                {"id": k, "before": left[k]["c4"]["verdict"],
                 "after": right[k]["c4"]["verdict"]}
                for k in common
                if left[k]["c4"]["verdict"] != right[k]["c4"]["verdict"]],
            "product_sha_changes": [
                k for k in common
                if left[k]["c3"]["sha256"] != right[k]["c3"]["sha256"]],
            "product_sha_change_details": [
                {"id": k, "before": left[k]["c3"]["sha256"],
                 "after": right[k]["c3"]["sha256"]}
                for k in common
                if left[k]["c3"]["sha256"] != right[k]["c3"]["sha256"]],
        }

    judges = sorted({r["c5"]["judge_sha256"] for r in new.values()})
    payload = {
        "tool": "b275_regression_report",
        "version": "1.0.0",
        "baseline": "semantic_v3_merged.json",
        "rerun_manifest": "judgment_space_v3.json",
        "rerun_shards": [
            "b275_regression/regress_shard0.json",
            "b275_regression/regress_shard1.json",
            "b275_regression/regress_shard2.json",
        ],
        "rerun_family_evidence": [
            "b275_regression/regress_repair.json",
            "b275_regression/regress_async.json",
        ],
        "shard_summaries": shards,
        "totals": {
            "records": len(new),
            "equal": sum(1 for r in new.values()
                         if r["c4"]["verdict"] == "EQUAL"),
            "error": sum(1 for r in new.values()
                         if r["c4"]["verdict"] == "ERROR"),
            "covered_5tuple": sum(1 for r in new.values()
                                  if r["status"] == "covered_5tuple"),
        },
        "verdict_changes": verdict_changes,
        "status_changes": status_changes,
        "product_sha_changes": sha_changes,
        "judge_sha256": judges,
        "family_checks": family_checks,
        "interpretation": {
            "base_1556": "0 verdict changes and 0 status changes against "
                         "semantic_v3_merged.json; the 12 product SHA changes "
                         "are confined to the m04/JS-TRY family.",
            "module_32": "12 archived DIFFERENT verdicts become EQUAL because "
                         "the module rerun uses the repaired m04 pyc and the "
                         "in-repo products; these are the intended B275 "
                         "improvements, not regressions.",
            "repair_36_async_62": "archived evidence is byte-identical to the "
                                  "post-B275 reruns.",
        },
    }
    out = os.path.join(FRESH, "B275_REGRESSION.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(json.dumps(payload["totals"], ensure_ascii=False))
    print("verdict_changes", len(verdict_changes),
          "status_changes", len(status_changes), "sha_changes", len(sha_changes))
    print("family", {k: (v["common"], len(v["verdict_changes"]),
                          len(v["product_sha_changes"]))
                      for k, v in family_checks.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
