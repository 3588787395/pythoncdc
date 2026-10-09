"""R14-03 复现电池：取反操作数中有一个是链式比较（a>b>c）时的负极性 and 链。

m02_plain_and_not 是 GREEN 对照（纯比较成员的 `not X and not Y` 折叠正确），
其余三例是 RED 缺陷例。判决只喂 pycdc 产物：见 ../DIAG_R1403_API_BASE_MERGE_AS_BODY.md。
跑法：python -X utf8 .trae/specs/.../rounds/round14/repro_ccneg/run_ccneg.py
"""
import os, py_compile, subprocess, sys, tempfile

D = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(__file__)
for _ in range(7):
    ROOT = os.path.dirname(ROOT)
TD = os.path.join(tempfile.gettempdir(), "r14ccneg")
os.makedirs(TD, exist_ok=True)
files = sorted(f for f in os.listdir(D) if f.endswith(".py") and f != "run_ccneg.py")
red = green = 0
for f in files:
    sp = os.path.join(D, f)
    pp = os.path.join(TD, f[:-3] + ".pyc")
    out = os.path.join(TD, f[:-3] + "_prod.py")
    for x in (pp, out):
        if os.path.exists(x):
            os.remove(x)
    py_compile.compile(sp, cfile=pp, doraise=True)
    subprocess.run([sys.executable, "-X", "utf8", "pycdc.py", "--region", pp, "-o", out],
                   capture_output=True, cwd=ROOT, timeout=280)
    r = subprocess.run([sys.executable, "-X", "utf8", "scripts/pyc_verify.py", "single", pp,
                        "--source", out], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=ROOT, timeout=280)
    txt = (r.stdout or "") + (r.stderr or "")
    v = [l for l in txt.splitlines() if "status=" in l]
    ok = bool(v) and "success_rate=100.00%" in v[0]
    green += 1 if ok else 0
    red += 0 if ok else 1
    prod = open(out, encoding="utf-8").read().splitlines()
    body = [l for l in prod if l.strip().startswith(("if ", "def ", "return", "x -="))]
    print("%-24s %-22s %s" % (f[:-3], (v[0].split("status=")[1][:20] if v else "NOVERDICT"),
                              " / ".join(b.strip() for b in body[:3])[:96]))
print("GREEN=%d RED=%d / %d" % (green, red, len(files)))
