# -*- coding: utf-8 -*-
"""Dump a rule_proof_check proof-records file: summary, per-reason rule
lists, and the manifest/REHEARSAL sections (249-basis derivation).

usage: python -X utf8 s3_dump_records.py <proof_records.json> [--rules R1,R2]
"""
import json
import sys


def main():
    doc = json.load(open(sys.argv[1], encoding="utf-8-sig"))
    rules = {r["rule_id"]: r for r in doc.get("rules", [])}
    print("== top keys:", list(doc.keys()))
    s = doc.get("summary") or {}
    print("== summary:", json.dumps(s, ensure_ascii=False)[:2000])
    mc = doc.get("manifest_check") or doc.get("rehearsal") or {}
    if mc:
        print("== manifest_check:", json.dumps(mc, ensure_ascii=False)[:1500])
    rf = doc.get("run_failures") or {}
    print("== run_failures:", json.dumps(rf, ensure_ascii=False)[:600])

    want = None
    if len(sys.argv) > 2 and sys.argv[2] == "--rules":
        want = set(x.strip() for x in sys.argv[3].split(","))
    by_reason = {}
    for rid, r in sorted(rules.items()):
        status = r.get("status")
        reasons = tuple(sorted(set(
            x.get("code") if isinstance(x, dict) else x
            for x in (r.get("reasons") or []))))
        if want and rid not in want:
            continue
        m = r.get("measurement") or {}
        t, f = m.get("evaluations_true", m.get("t")), m.get("evaluations_false", m.get("f"))
        line = "%-22s %-8s t=%-5s f=%-5s so=%-5s %s %s" % (
            rid, status, t, f, r.get("symbol_observed"),
            ",".join(reasons) or "-", (r.get("notes") or [])[:3])
        print(line)
        if status != "proved":
            by_reason.setdefault(reasons, []).append(rid)
    print("\n== open by reason group:")
    for reasons, rids in sorted(by_reason.items(), key=lambda kv: -len(kv[1])):
        print("  %-60s (%d): %s" % (",".join(reasons), len(rids),
                                    " ".join(rids)))


if __name__ == "__main__":
    main()
