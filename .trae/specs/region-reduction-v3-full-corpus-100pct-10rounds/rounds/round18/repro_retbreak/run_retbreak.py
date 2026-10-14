"""R15-10 电池的常驻跑器（此前该目录只有 4 个源形、无 runner，每位工程师要自己重拼判决命令）。

判决只喂 `pycdc.py --region` 产物 + `scripts/pyc_verify.py single`；手写源当 --source 一律作废。
基线（landed 字节，2026-10-09 复量）：r01 红 / r02 红 / r03 绿 / r04 绿。
注意 r02 名义上是「控制例」，但实测因**第二缺陷**（`while…else` 的 else 子句丢失）而红，
所以它是红而**不是**本票靶子；用本电池判回归时按「r01/r02 只可转绿不可新增红、r03/r04 必须保持绿」读。

跑法：python -X utf8 .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round18/repro_retbreak/run_retbreak.py
"""
import os, py_compile, subprocess, sys, tempfile

D = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(__file__)
for _ in range(7):
    ROOT = os.path.dirname(ROOT)
TD = os.path.join(tempfile.gettempdir(), "r18retbreak")
os.makedirs(TD, exist_ok=True)
EXPECT = {"r01_return_arm_then_tail": "RED", "r02_break_arm_control": "RED",
          "r03_return_in_else_suite": "GREEN", "r04_two_return_arms": "GREEN"}
files = sorted(f for f in os.listdir(D) if f.endswith(".py") and not f.startswith("run_"))
red = green = drift = 0
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
    if not v:
        print("%-28s NOVERDICT (judge printed nothing)" % f[:-3])
        drift += 1
        continue
    ok = "status=success" in v[0]
    got = "GREEN" if ok else "RED"
    green += 1 if ok else 0
    red += 0 if ok else 1
    drift += 0 if got == EXPECT.get(f[:-3], got) else 1
    body = [l.strip() for l in open(out, encoding="utf-8").read().splitlines()
            if l.strip() and not l.strip().startswith("#")]
    print("%-28s %-5s exp=%-5s %s | %s" % (f[:-3], got, EXPECT.get(f[:-3], "?"),
                                           v[0].strip()[:34], " / ".join(body[2:6])[:70]))
print("GREEN=%d RED=%d DRIFT_VS_BASELINE=%d / %d" % (green, red, drift, len(files)))
