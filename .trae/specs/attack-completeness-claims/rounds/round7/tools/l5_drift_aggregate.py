"""Aggregate l5_drift_*.json files: per-chunk and grand unit totals."""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(os.path.dirname(HERE), "logs")


def main():
    files = sorted(glob.glob(os.path.join(LOGS, "l5_drift_*.json")))
    if not files:
        print("no drift files in %s" % LOGS)
        return
    for f in files:
        with open(f, "r", encoding="utf-8") as h:
            d = json.load(h)
        rows = d.get("rows", [])
        statuses = {}
        succ = tot = 0
        non_success = []
        for r in rows:
            s = r.get("status")
            statuses[s] = statuses.get(s, 0) + 1
            us = r.get("units_success")
            ut = r.get("units_total")
            if isinstance(us, int) and isinstance(ut, int):
                succ += us
                tot += ut
            if s != "success":
                non_success.append(r.get("path", "?"))
        print("%s range=%s rows=%d units_success=%d units_total=%d statuses=%s" % (
            os.path.basename(f), d.get("range"), len(rows), succ, tot, statuses))
        for p in non_success[:10]:
            print("  NON-SUCCESS: %s" % str(p)[:120])
    g_rows = 0
    g_succ = 0
    g_tot = 0
    for f in files:
        with open(f, "r", encoding="utf-8") as h:
            d = json.load(h)
        rows = d.get("rows", [])
        g_rows += len(rows)
        for r in rows:
            us = r.get("units_success")
            ut = r.get("units_total")
            if isinstance(us, int) and isinstance(ut, int):
                g_succ += us
                g_tot += ut
    print("GRAND rows=%d units_success=%d units_total=%d" % (g_rows, g_succ, g_tot))


if __name__ == "__main__":
    main()
