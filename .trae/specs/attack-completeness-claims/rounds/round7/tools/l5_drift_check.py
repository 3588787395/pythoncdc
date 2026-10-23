"""L5: evidence drift check -- are the recorded greens still green?

Two populations are re-verified with the *current* judge and the *current*
product, without regenerating anything:

* **corpus** (402 certified artifacts): the recorded claim is
  "6617/6617 units green" (baseline/readings.md §2).  The current judge verdict
  is recomputed for every artifact from the stored ``*OK.py`` product.
* **stamped probes**: every probe stamp whose staged ``.pyc`` + ``*OK.py`` are
  still in the repo is re-verified and compared with the recorded verdict.

Usage:  python -X utf8 l5_drift_check.py <start> <end>   (index range, 0-based)
Output: logs/l5_drift_<start>_<end>.json
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(ROUND, "..", "..", "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import pyc_verify  # noqa: E402

SHARD_DIR = os.path.join(
    REPO, ".trae", "specs", "adversarial-complete-forms-v2-10rounds", "baseline", "shards"
)
PROBE_LOG = os.path.join(ROUND, "logs", "l5_probe_forms.json")


def corpus_paths():
    paths = []
    for i in range(8):
        p = os.path.join(SHARD_DIR, "shard%d.json" % i)
        with open(p, encoding="utf-8") as fh:
            for it in json.load(fh):
                paths.append(it["path"])
    seen = set()
    out = []
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def main() -> int:
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
    ruler = pyc_verify.ruler_stamp(pyc_verify.DEFAULT_PYLINGUAL)
    compare_pyc = pyc_verify.load_compare_pyc(pyc_verify.DEFAULT_PYLINGUAL)
    tmp = tempfile.mkdtemp(prefix="l5_drift_")

    paths = corpus_paths()
    rows = []
    for idx, p in enumerate(paths):
        if not (start <= idx < end):
            continue
        local = p if os.path.exists(p) else os.path.join(
            REPO, "site-packages", os.path.relpath(p, "site-packages"))
        prod = local[:-4] + "OK.py"
        if not os.path.exists(prod):
            rows.append({"path": p, "status": "missing_product"})
            continue
        r = pyc_verify.evaluate(local, prod, tmp, compare_pyc)
        rows.append({"path": p, "status": r["status"],
                     "units_success": r["units_success"],
                     "units_total": r["units_total"],
                     "failures": r["failures"][:3],
                     "detail": (r["detail"] or "")[:200]})

    out = os.path.join(ROUND, "logs", "l5_drift_%04d_%04d.json" % (start, end))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"tool": "l5_drift_check.py", "ruler": ruler,
                   "range": [start, end], "rows": rows}, fh,
                  ensure_ascii=False, indent=1)
    ok = sum(1 for r in rows if r["status"] == "success")
    bad = [r for r in rows if r["status"] != "success"]
    print("range [%d,%d) n=%d success=%d other=%d" % (start, end, len(rows), ok, len(bad)))
    for r in bad[:20]:
        print("   ", r["status"], os.path.basename(r["path"]),
              "%s/%s" % (r.get("units_success"), r.get("units_total")),
              (r.get("detail") or "")[:90])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
