# -*- coding: utf-8 -*-
"""1) Show exemption annotation of exempted rules; 2) classify the (a)15
tool-path rules (from classification_65.json) in the final records; 3) print
the 249-basis (excluding (a)15) reading."""
import json
import sys

rec_path = sys.argv[1]
cls_path = sys.argv[2]
rec = json.load(open(rec_path, encoding="utf-8-sig"))
rules = {r["rule_id"]: r for r in rec["rules"]}

print("== exemption annotation of the 4 exempted rules ==")
for rid in ("RULE-2b6f0dcd703d", "RULE-e7701666d7b5", "RULE-ed5bec7d7a05",
            "RULE-a310f7ea600b"):
    r = rules[rid]
    keys = [k for k in r if "exemp" in k or "structural" in k]
    print(rid, r["symbol"], "status=", r["status"],
          "exemption_keys=", keys)
    for k in keys:
        v = r[k]
        s = json.dumps(v, ensure_ascii=False)
        print("   ", k, "=", s[:220])

cls = json.load(open(cls_path, encoding="utf-8-sig"))
groups = cls.get("groups") or cls.get("classes") or cls
# find (a) group rules regardless of schema
a_rules = sorted(set(rr["rule_id"] for rr in cls["rules"] if rr.get("class") == "a"))
print("\n== (a)15 tool-path rules ==", len(a_rules))
in_rec = 0
prov = 0
for rid in a_rules:
    r = rules.get(rid)
    if r is None:
        print(rid, "NOT-IN-264-RECORDS")
        continue
    in_rec += 1
    if r["status"] == "proved":
        prov += 1
    print(rid, r["symbol"], r["status"],
          "reasons=", ",".join(r.get("reason_codes", []))[:60])
print(f"(a)-rules in records: {in_rec}, proved among them: {prov}")

print("\n== 249-basis reading (264 minus (a)15) ==")
tot = len(rec["rules"]) - in_rec
pr = sum(1 for r in rec["rules"] if r["rule_id"] not in a_rules and r["status"] == "proved")
op = tot - pr
print(f"total={tot} proved={pr} open={op}")
strict = sum(1 for r in rec["rules"] if r["rule_id"] not in a_rules
             and r["status"] == "proved" and not r.get("structural_negative_exemption"))
ex = pr - strict
print(f"strict={strict} exempted={ex}")
reasons = {}
for r in rec["rules"]:
    if r["rule_id"] in a_rules or r["status"] == "proved":
        continue
    for c in r.get("reason_codes", []):
        reasons[c] = reasons.get(c, 0) + 1
print("open reasons:", dict(sorted(reasons.items())))
