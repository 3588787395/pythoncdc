"""Task 0.5 before reading: run pyc_verify.py single on each real-origin offcorpus sample."""
import json
import os
import re
import subprocess
import sys

SAMPLES = r".trae\specs\attack-completeness-claims\rounds\round6\offcorpus\samples.json"
OFFCORPUS = r".trae\specs\attack-completeness-claims\rounds\round6\offcorpus"
BASE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(BASE, "..", "..", "..", "..", "..", ".."))
OUT_DIR = os.path.join(BASE, "real46")

data = json.load(open(SAMPLES, encoding="utf-8"))
samples = data["samples"] if isinstance(data, dict) else data
real = [s for s in samples if s.get("origin") == "real"]
print(f"samples total={len(samples)} real={len(real)} "
      f"non_real={len(samples) - len(real)}", flush=True)

pat = re.compile(r"\[single\] status=(\S+) units=(\d+)/(\d+) success_rate=([\d.]+%|-)")
results = {}
for idx, s in enumerate(real, 1):
    slug = s["slug"]
    pyc = os.path.join(OFFCORPUS, slug + ".pyc")
    if not os.path.exists(pyc):
        results[slug] = {"status": "MISSING_PYC", "units": "", "success_rate": ""}
        print(f"[{idx}/{len(real)}] {slug}: MISSING_PYC", flush=True)
        continue
    try:
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", os.path.join("scripts", "pyc_verify.py"), "single", pyc],
            capture_output=True, text=True, timeout=300,
            cwd=REPO_ROOT)
    except subprocess.TimeoutExpired:
        results[slug] = {"status": "TIMEOUT", "units": "", "success_rate": ""}
        print(f"[{idx}/{len(real)}] {slug}: TIMEOUT", flush=True)
        continue
    m = pat.search(proc.stdout)
    if m:
        status, u_ok, u_tot, rate = m.group(1), m.group(2), m.group(3), m.group(4)
        results[slug] = {"status": status, "units": f"{u_ok}/{u_tot}", "success_rate": rate}
        print(f"[{idx}/{len(real)}] {slug}: status={status} units={u_ok}/{u_tot} rate={rate}",
              flush=True)
    else:
        tail = (proc.stdout or "")[-200:].replace("\n", " | ")
        results[slug] = {"status": "NO_MATCH", "units": "", "success_rate": "", "tail": tail}
        print(f"[{idx}/{len(real)}] {slug}: NO_MATCH rc={proc.returncode} tail={tail}", flush=True)

with open(os.path.join(OUT_DIR, "real46_before.json"), "w", encoding="utf-8") as f:
    json.dump({"count": len(results), "results": results}, f, ensure_ascii=False, indent=1)

ok_files = sum(1 for r in results.values() if r["status"] == "success")
all_units = 0
ok_units = 0
for r in results.values():
    if "/" in r.get("units", ""):
        a, b = r["units"].split("/")
        ok_units += int(a)
        all_units += int(b)
print(f"REAL46 DONE: files={len(results)} success_files={ok_files} units={ok_units}/{all_units}",
      flush=True)
