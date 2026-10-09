"""Round-19 test-engineer battery: 「共用尾 / 隐式 return None 汇合」 family.

Residual units assigned to this family by the sealed round-18 roster:
  trade_info_utils.query_strategy_id   JUMP_FORWARD->shared tail written as inline LOAD_CONST None;RETURN_VALUE (+ shared tail 2 条未发)
  trade_info_utils.query_trade_strategy_info  net 0 = two inline (+1) + one missing shared tail (-2)
  handlers.TWHThreadController._target  pair LOAD_CONST None / RETURN_VALUE not emitted
  real_quote.RealQuoteData.get_real_minute_kline  -2 压形
  wizard_quant_api.filter_desicion      -2
  quote.Quote.get_real_from_zeromq      extra JUMP_FORWARD skipping the shared `return None, flag` tail

Writes the shape sources into $PWD/../src, then (with --run) compiles each, decompiles with
the repo's pycdc.py --region, and judges ONLY the product via scripts/pyc_verify.py single.
usage: python -X utf8 make_tail.py [--run]
"""
import os, py_compile, subprocess, sys, tempfile

SHAPES = {
    # --- early return + shared tail ---
    "t01_else_bare_return_tail_value": """
def f(a):
    if a > 0:
        y = 1
    else:
        return
    return y
""",
    "t02_two_bare_returns_tail_tuple": """
def f(a, b):
    if a:
        return
    if b:
        return
    return None, b
""",
    "t03_elif_all_fall_to_tail": """
def f(a, b):
    if a:
        x = 1
    elif b:
        x = 2
    else:
        x = 3
    return None, x
""",
    "t04_nested_if_returns_tail_none": """
def f(a, b):
    if a:
        if b:
            return
        x = 1
    else:
        x = 2
    return
""",
    "t05_while_else_then_tail": """
def f(items):
    for it in items:
        if it:
            break
    else:
        return
    return it
""",
    "t06_bool_cond_two_exits": """
def f(a, b):
    if a and b:
        return
    return None, a
""",
    "t07_chained_compare_tail": """
def f(v, lo, hi):
    if not lo < v <= hi:
        return
    return None, v
""",
    "t08_try_body_tail_none": """
def f(a):
    try:
        if a:
            return
    except ValueError:
        return
    return None, a
""",
    "t09_loop_inside_if_tail": """
def f(a, items):
    if a:
        for it in items:
            if it > 0:
                return
    return None, a
""",
    "t10_two_returns_same_value": """
def f(a):
    if a:
        return None
    return None
""",
    # --- GREEN controls: plain shapes that must already decompile byte-exactly ---
    "g01_plain_if_return_value": """
def f(a):
    if a:
        return 1
    return 2
""",
    "g02_plain_elif_else_assign": """
def f(a, b):
    if a:
        x = 1
    elif b:
        x = 2
    else:
        x = 3
    return x
""",
    "g03_while_no_break_tail": """
def f(items):
    for it in items:
        if it:
            print(it)
    return 0
""",
}

D = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(D, "src")
os.makedirs(SRC, exist_ok=True)
ROOT = os.path.abspath(os.path.join(D, *(['..'] * 6)))
TD = os.path.join(tempfile.gettempdir(), "r19tail")
os.makedirs(TD, exist_ok=True)

for name, body in SHAPES.items():
    with open(os.path.join(SRC, name + ".py"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body.lstrip("\n"))

if "--run" not in sys.argv:
    print("wrote %d shapes to %s" % (len(SHAPES), SRC))
    raise SystemExit(0)

red = green = 0
for name in sorted(SHAPES):
    sp = os.path.join(SRC, name + ".py")
    pp = os.path.join(TD, name + ".pyc")
    out = os.path.join(TD, name + "_prod.py")
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
    prod = [l for l in open(out, encoding="utf-8").read().splitlines()
            if l.strip() and not l.strip().startswith("#")]
    print("%-34s %-14s %s" % (name, "GREEN" if ok else "RED",
                              " | ".join(p.strip() for p in prod[2:8])[:88]))
print("GREEN=%d RED=%d / %d" % (green, red, len(SHAPES)))
