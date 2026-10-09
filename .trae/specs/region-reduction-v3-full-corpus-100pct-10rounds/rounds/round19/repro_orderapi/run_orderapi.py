"""T19-4 复现电池：三元的条件测试与「宿主调用前缀」融在同一个基本块里。

缺陷形（RED）：`log.info('a{side}b'.format(side=(... if c ... else ...)))` —— CPython 把
`log.info` / `.format` 的求值前缀和三元的条件测试放进同一个基本块，识别端把整块登记成
`TernaryRegion` 的 entry/condition_block，发射端只发出裸三元，宿主调用整条语句消失。
GREEN 对照：o2（关键字实参里没有三元）、o3（三元先赋值给局部变量再用作实参）。
判决只喂 pycdc --region 产物：见 ../DIAG_R1515_ORDERAPI_TERNARY_HOST_PREFIX.md
跑法：python -X utf8 .trae/specs/.../rounds/round19/repro_orderapi/run_orderapi.py
"""
import os, py_compile, subprocess, sys, tempfile

D = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(__file__)
for _ in range(7):
    ROOT = os.path.dirname(ROOT)
TD = os.path.join(tempfile.gettempdir(), "r19orderapi")
os.makedirs(TD, exist_ok=True)
files = sorted(f for f in os.listdir(D) if f.endswith(".py") and not f.startswith("run_"))
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
    ok = bool(v) and "status=success" in v[0]
    green += 1 if ok else 0
    red += 0 if ok else 1
    prod = open(out, encoding="utf-8").read().splitlines()
    body = [l for l in prod if l.strip() and not l.strip().startswith("#")]
    print("%-28s %-26s %s" % (f[:-3], (v[0].strip()[:26] if v else "NOVERDICT"),
                              " | ".join(b.strip() for b in body[2:5])[:100]))
print("GREEN=%d RED=%d / %d" % (green, red, len(files)))
