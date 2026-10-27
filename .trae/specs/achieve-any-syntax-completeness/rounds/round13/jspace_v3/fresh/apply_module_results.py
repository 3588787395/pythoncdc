#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply the 32 module-family C4 results to the manifest.

Only ``EQUAL`` records may stay callable.  A ``DIFFERENT`` record whose diffs
are all R7 is a code-object defect and must be explicitly excluded with the R7
reason instead of being silently counted.  The filtered evidence keeps only
the EQUAL records for the merge; the full evidence stays on disk as the defect
record.

The historical repaired ``m04`` family was R7-blocked because the product
added an extra nested ``try`` (B275).  After the B275 fix in
``core/cfg/region_ast_generator.py`` all 32 module-family records are EQUAL;
this script still applies the same verdict-driven policy, so a future R7
regression cannot slip into the numerator.

Run after ``semantic_runner.py``:

    python -X utf8 .../fresh/apply_module_results.py \
        --space .../judgment_space_v3m.json \
        --evidence .../semantic_module_b275.json \
        --out-space .../judgment_space_v3m_b275.json \
        --out-evidence .../semantic_module_equal_b275.json \
        --report .../module_results_b275_report.json
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import sys


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def dump(path: str, payload: dict) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--out-space", required=True)
    parser.add_argument("--out-evidence", required=True)
    parser.add_argument("--report", default="")
    args = parser.parse_args(argv)

    space = load(args.space)
    evidence = load(args.evidence)
    records = {record.get("entry_id"): record for record in evidence.get("records", [])
               if isinstance(record, dict)}
    equal_records = []
    counts = collections.Counter()
    rows = []
    entries = []
    for entry in space.get("entries", []):
        item = dict(entry)
        eid = item.get("id")
        record = records.get(eid)
        if item.get("derivation") != "module_code_witness" or record is None:
            entries.append(item)
            continue
        verdict = record.get("c4", {}).get("verdict")
        diffs = record.get("c4", {}).get("diffs") or []
        counts[verdict] += 1
        if verdict == "EQUAL":
            item["excluded"] = []
            item["status"] = "callable"
            equal_records.append(record)
            rows.append({"id": eid, "verdict": verdict, "action": "covered"})
        else:
            only_r7 = bool(diffs) and all(str(diff) == "R7" for diff in diffs)
            reason = ("r7_code_object_diff: module-code witness product differs only in "
                      "co_code/co_exceptiontable (extra nested try)" if only_r7 else
                      "module_code_witness_failed: %s" % ",".join(str(d) for d in diffs))
            item["excluded"] = [reason]
            item["status"] = "excluded"
            item["derivation"] = ("module_code_witness_r7_blocked" if only_r7 else
                                  "module_code_witness_failed")
            item.setdefault("call_static", {}).setdefault("module_code_witness", {})[
                "result"] = {"verdict": verdict, "diffs": diffs, "action": "excluded",
                             "reason": reason}
            rows.append({"id": eid, "verdict": verdict, "action": "excluded",
                         "reason": reason})
        entries.append(item)

    out_space = dict(space)
    out_space["entries"] = entries
    out_space["module_family_results"] = {
        "tool": "apply_module_results", "counts": dict(sorted(counts.items())),
        "equal": len(equal_records), "rows": rows,
    }
    dump(args.out_space, out_space)
    dump(args.out_evidence, {"tool": "apply_module_results", "records": equal_records,
                             "summary": {"equal": len(equal_records)}})
    if args.report:
        dump(args.report, out_space["module_family_results"])
    print("[module-results] counts=%s equal=%d" % (dict(sorted(counts.items())), len(equal_records)))
    for row in rows:
        if row["action"] != "covered":
            print("[module-results] excluded %s: %s" % (row["id"], row.get("reason")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
