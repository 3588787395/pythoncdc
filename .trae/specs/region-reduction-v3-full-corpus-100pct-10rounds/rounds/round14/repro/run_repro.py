"""R14-01 复现电池：or 链的末操作数是链式比较（`a < b < c`）。

用法（仓库根，必须用 3.11 解释器）:
    python -X utf8 .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round14/repro/run_repro.py

判据只接受 **pycdc 产物** 作为 --source。用手写的原始 .py 作 --source 是空判据
（原始文件必然编成自己的字节码），见 ../DIAG_R1401_OR_CHAIN_CC_TAIL.md §1。
"""
import os, py_compile, subprocess, sys, tempfile

D = os.path.dirname(os.path.abspath(__file__))
TD = os.path.join(tempfile.gettempdir(), "r14repro")
os.makedirs(TD, exist_ok=True)
ROOT = os.path.abspath(__file__)
for _ in range(7):
    ROOT = os.path.dirname(ROOT)
files = sorted(f for f in os.listdir(D) if f.endswith(".py") and f != "run_repro.py"
               and not f.endswith("_prod.py"))
bad = 0
for f in files:
    sp = os.path.join(D, f)
    pp = os.path.join(TD, f[:-3] + ".pyc")
    out = os.path.join(TD, f[:-3] + "_prod.py")
    py_compile.compile(sp, cfile=pp, doraise=True)
    subprocess.run([sys.executable, "-X", "utf8", "pycdc.py", "--region", pp, "-o", out],
                   capture_output=True, cwd=ROOT, timeout=280)
    r = subprocess.run([sys.executable, "-X", "utf8", "scripts/pyc_verify.py", "single", pp,
                        "--source", out], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=ROOT, timeout=280)
    txt = (r.stdout or "") + (r.stderr or "")
    v = [l for l in txt.splitlines() if "status=" in l]
    ok = bool(v) and "success_rate=100.00%" in v[0]
    bad += 0 if ok else 1
    print("%-28s %s" % (f, (v[0].split("status=")[1][:36] if v else "NOVERDICT")))
print("RED=%d / %d  ROOT=%s" % (bad, len(files), ROOT))
