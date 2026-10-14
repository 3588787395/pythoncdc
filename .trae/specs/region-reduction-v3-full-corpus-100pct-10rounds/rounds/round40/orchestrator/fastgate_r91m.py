"""Fast gates for _sync_worker mechanism A candidates: 12-line repro + round-14 battery.

usage: python -X utf8 fastgate_r91m.py [--gen CANDIDATE_GEN] [--ana CANDIDATE_ANA] [--full]

Omits either flag to keep the landed file. Prints, in order: both sha16s actually installed, the
12-line duplicated-while-test repro verdict (the acceptance signal for mechanism A: it must go 1/2 ->
2/2), the nine-case round-14 battery count (a NO-REGRESSION witness for the neighbouring if/elif
chained-compare family: it must stay at RED=8/9), and per-unit windows for `_sync_worker`.
`--full` additionally regenerates and judges the no-regression panel.
"""
import argparse
import os
import py_compile
import shutil
import subprocess
import sys

REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
M = r"D:/Temp/r91m"
SPEC = os.path.join(REPO, ".trae/specs/region-reduction-v3-full-corpus-100pct-10rounds")
REPRO = os.path.join(SPEC, "rounds/round40/r90/repro/repro_rotated_while.pyc")
# the MIRROR copy, because the runner derives ROOT from its own __file__: the repo
# copy would grade the repo's landed bytes no matter what is installed here.
BATT = os.path.join(M, ".trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round14/repro/run_repro.py")
GEN = os.path.join("core/cfg/region_ast_generator.py")
ANA = os.path.join("core/cfg/region_analyzer.py")

ap = argparse.ArgumentParser()
ap.add_argument("--gen", default="")
ap.add_argument("--ana", default="")
ap.add_argument("--full", action="store_true")
A = ap.parse_args()

for src, dst in ((A.gen, GEN), (A.ana, ANA)):
    if src:
        shutil.copyfile(src, os.path.join(M, dst))
ppc = os.path.join(M, "core/cfg/__pycache__")
if os.path.isdir(ppc):
    shutil.rmtree(ppc)
tpc = os.path.join(M, ".trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round14/repro/__pycache__")
if os.path.isdir(tpc):
    shutil.rmtree(tpc)


def sha16(path):
    import hashlib
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


for f in (GEN, ANA):
    py_compile.compile(os.path.join(M, f), doraise=True)
print("[installed] gen=%s ana=%s" % (sha16(os.path.join(M, GEN)), sha16(os.path.join(M, ANA))))


def run(cmd, cwd):
    r = subprocess.run([sys.executable, "-X", "utf8"] + cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=cwd, timeout=280)
    return (r.stdout or "") + (r.stderr or "")


out = os.path.join(M, "out")
os.makedirs(out, exist_ok=True)

prod = os.path.join(out, "fastgate_repro.py")
run([os.path.join(M, "pycdc.py"), REPRO, "-o", prod], M)
log = run([os.path.join(REPO, "scripts/pyc_verify.py"), "single", REPRO, "--source", prod], M)
hit = [l for l in log.splitlines() if "status=" in l or "Failure" in l]
print("[repro mechanism A] " + " / ".join(x.strip() for x in hit[-2:]))

log = run([BATT], M)
tail = [l for l in log.splitlines() if l.strip()][-1]
print("[battery no-regression] " + tail.strip())

if A.full:
    broker = os.path.join(REPO, "site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc")
    prod = os.path.join(out, "fastgate_broker.py")
    run([os.path.join(M, "pycdc.py"), broker, "-o", prod], M)
    log = run([os.path.join(REPO, "scripts/pyc_verify.py"), "single", broker, "--source", prod], M)
    hit = [l for l in log.splitlines() if "status=" in l or "Failure" in l]
    print("[broker] " + " / ".join(x.strip() for x in hit[-2:]))
    log = run([os.path.join(M, "win_r91.py"), broker, "_sync_worker", prod], M)
    keep = [l for l in log.splitlines() if l.startswith(("orig instrs", "== #", "windows="))]
    print("[_sync_worker windows] " + (keep[-1] if keep else "RIG FAILED"))
    for name, p in (("realtime", "IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc"),
                    ("function", "IQEngine/plugins/plugin_system_risk_calculation/function.pyc"),
                    ("replace_utils", "IQCommon/util/replace_utils.pyc"),
                    ("quote", "fly/data/quote.pyc"),
                    ("quotation", "fly/data/quotation.pyc"),
                    ("order_api", "IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc")):
        pyc = os.path.join(REPO, "site-packages", p)
        if not os.path.exists(pyc):
            print("[panel %s] MISSING pyc path" % name)
            continue
        pr = os.path.join(out, "fastgate_%s.py" % name)
        run([os.path.join(M, "pycdc.py"), pyc, "-o", pr], M)
        log = run([os.path.join(REPO, "scripts/pyc_verify.py"), "single", pyc, "--source", pr], M)
        hit = [l for l in log.splitlines() if "status=" in l]
        print("[panel %s] %s" % (name, hit[-1].strip() if hit else "NO VERDICT LINE"))
