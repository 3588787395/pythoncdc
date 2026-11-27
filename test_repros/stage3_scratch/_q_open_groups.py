# -*- coding: utf-8 -*-
"""List v4 open rules grouped by reason code, with so/t/f and weak-neg notes."""
import json
import sys

doc = json.load(open(sys.argv[1], encoding="utf-8-sig"))
groups = {}
for r in doc["rules"]:
    if r.get("status") == "proved":
        continue
    m = r.get("measurement") or {}
    reasons = tuple(sorted(x.get("code") if isinstance(x, dict) else x
                           for x in (r.get("reasons") or [])))
    groups.setdefault(reasons, []).append((r["rule_id"], r.get("symbol_observed"),
                                          m.get("true_evaluations"),
                                          m.get("false_evaluations"),
                                          m.get("pyc_runs_with_true"),
                                          m.get("pyc_runs_false_only"),
                                          m.get("anchors_located"),
                                          m.get("anchors_declared"),
                                          r.get("rule_symbol") or r.get("symbol")))
for reasons, rows in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print("== %s (%d)" % (",".join(reasons), len(rows)))
    for rid, so, t, f, rt, rf, al, ad, sym in rows:
        print("  %-22s so=%-5s t=%-5s f=%-6s runs_t=%-4s runs_f=%-4s a=%s/%s %s"
              % (rid, so, t, f, rt, rf, al, ad, sym or ""))
