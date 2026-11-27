# -*- coding: utf-8 -*-
"""Query specific rules in a proof-records json (works for huge files)."""
import json
import sys

doc = json.load(open(sys.argv[1], encoding="utf-8-sig"))
want = set(sys.argv[2].split(","))
rules = {r["rule_id"]: r for r in doc.get("rules", [])}
for rid in sorted(want):
    r = rules.get(rid)
    if not r:
        print("%-22s NOT IN FILE" % rid)
        continue
    m = r.get("measurement") or {}
    reasons = ",".join(x.get("code") if isinstance(x, dict) else x
                       for x in (r.get("reasons") or [])) or "-"
    w = r.get("witnesses") or {}
    negsel = (r.get("witness_evidence") or {}).get("negative_selection")
    print("%-22s %-7s so=%-5s t=%-4s f=%-4s runs_t=%-3s runs_f=%-3s neg=%-22s %s"
          % (rid, r.get("status"), r.get("symbol_observed"),
             m.get("true_evaluations"), m.get("false_evaluations"),
             m.get("pyc_runs_with_true"), m.get("pyc_runs_false_only"),
             negsel or (w.get("negative") or ["-"])[0][:22], reasons))
