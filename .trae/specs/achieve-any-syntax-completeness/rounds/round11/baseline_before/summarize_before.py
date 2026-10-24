"""Aggregate Task 0.5 before readings from pyc_verify batch reports (402 shards + small34)."""
import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)))

rows = []
gf = gu = guok = 0
for i in range(8):
    p = os.path.join(OUT, "g5_402", f"shard{i}_report.json")
    d = json.load(open(p, encoding="utf-8"))
    st = d["files_by_status"]
    gf += d["files_total"]
    gu += d["units_total"]
    guok += d["units_success"]
    rows.append({
        "shard": i,
        "files": d["files_total"],
        "success": st["success"], "failure": st["failure"],
        "compile_error": st["compile_error"], "error": st["error"],
        "units_success": d["units_success"], "units_total": d["units_total"],
        "success_rate": d["success_rate"],
        "elapsed_sec": d["elapsed_sec"],
        "generated_at": d["generated_at"],
        "ruler_sha": d["ruler"]["compare_pyc_sha256"],
    })

d = json.load(open(os.path.join(OUT, "g5_small34", "small34_report.json"), encoding="utf-8"))
st = d["files_by_status"]
small34 = {
    "files": d["files_total"], "success": st["success"], "failure": st["failure"],
    "compile_error": st["compile_error"], "error": st["error"],
    "units_success": d["units_success"], "units_total": d["units_total"],
    "success_rate": d["success_rate"], "elapsed_sec": d["elapsed_sec"],
    "generated_at": d["generated_at"],
}

summary = {
    "g5_402": {
        "shards": rows,
        "files_total": gf,
        "units_success": guok,
        "units_total": gu,
        "units_rate": round(guok / gu, 6) if gu else None,
    },
    "g5_small34": small34,
}
with open(os.path.join(OUT, "g5_before_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)

for r in rows:
    print(f"shard{r['shard']}: files={r['files']} status={r['success']}/{r['failure']}"
          f"/{r['compile_error']}/{r['error']} units={r['units_success']}/{r['units_total']}"
          f" rate={r['success_rate']} elapsed={r['elapsed_sec']}s")
print(f"402 TOTAL: files={gf} units={guok}/{gu}")
s = small34
print(f"small34: files={s['files']} status={s['success']}/{s['failure']}/{s['compile_error']}/{s['error']}"
      f" units={s['units_success']}/{s['units_total']} rate={s['success_rate']} elapsed={s['elapsed_sec']}s")
