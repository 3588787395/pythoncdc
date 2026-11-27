# -*- coding: utf-8 -*-
"""Stage-3 B1 regression comparator.

usage: python -X utf8 compare_b1.py <old_proof_records.json> \
           <new_proof_records.json> <out.json>

Compares two rule_proof_check proof-record files:
  * regressions       old proved -> new not proved (must stay empty)
  * newly_proved      old open -> new proved (with measurement deltas)
  * run_failures      added / removed / kept
  * status flip detail per rule (symbol, reasons, t/f, symbol_observed)
"""
import json
import sys


def load(path):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def index(doc):
    rules = doc.get("rules") or doc.get("records") or []
    return {r["rule_id"]: r for r in rules}


def summ(r):
    """compact per-rule measurement snapshot for flip detail"""
    m = r.get("measurement") or {}
    return {
        "status": r.get("status"),
        "symbol": r.get("symbol"),
        "reasons": [x.get("code") if isinstance(x, dict) else x
                    for x in (r.get("reasons") or [])],
        "notes": r.get("notes") or [],
        "measurement": m,
        "symbol_observed": r.get("symbol_observed"),
        "witnesses": r.get("witnesses") or {},
    }


def main():
    old_doc, new_doc = load(sys.argv[1]), load(sys.argv[2])
    old_r, new_r = index(old_doc), index(new_doc)
    regressions, newly_proved, other_flips = [], [], []
    for rid in sorted(new_r):
        nr, orr = new_r[rid], old_r.get(rid)
        if orr is None:
            continue
        os_, ns = orr.get("status"), nr.get("status")
        if os_ == ns:
            continue
        if os_ == "proved" and ns != "proved":
            regressions.append({"rule_id": rid, "symbol": nr.get("symbol"),
                                "old": summ(orr), "new": summ(nr)})
        elif os_ != "proved" and ns == "proved":
            newly_proved.append({"rule_id": rid, "symbol": nr.get("symbol"),
                                 "old": summ(orr), "new": summ(nr)})
        else:
            other_flips.append({"rule_id": rid, "symbol": nr.get("symbol"),
                                "old_status": os_, "new_status": ns})
    old_rf = old_doc.get("run_failures") or {}
    new_rf = new_doc.get("run_failures") or {}
    out = {
        "old": sys.argv[1],
        "new": sys.argv[2],
        "old_summary": old_doc.get("summary"),
        "new_summary": new_doc.get("summary"),
        "regressions": regressions,
        "regression_count": len(regressions),
        "newly_proved": newly_proved,
        "newly_proved_count": len(newly_proved),
        "other_status_flips": other_flips,
        "old_run_failures": old_rf,
        "new_run_failures": new_rf,
        "run_failures_added": {k: v for k, v in new_rf.items()
                               if k not in old_rf},
        "run_failures_removed": {k: v for k, v in old_rf.items()
                                 if k not in new_rf},
        "zero_regression": len(regressions) == 0,
    }
    with open(sys.argv[3], "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("[compare_b1] regressions=%d newly_proved=%d other_flips=%d "
          "run_failures old=%d new=%d added=%d zero_regression=%s"
          % (len(regressions), len(newly_proved), len(other_flips),
             len(old_rf), len(new_rf), len(out["run_failures_added"]),
             out["zero_regression"]))
    for f in newly_proved:
        print("  +proved %s %s" % (f["rule_id"], f["symbol"]))
    for f in regressions:
        print("  REGRESSION %s %s" % (f["rule_id"], f["symbol"]))
    return 0 if out["zero_regression"] else 1


if __name__ == "__main__":
    sys.exit(main())
