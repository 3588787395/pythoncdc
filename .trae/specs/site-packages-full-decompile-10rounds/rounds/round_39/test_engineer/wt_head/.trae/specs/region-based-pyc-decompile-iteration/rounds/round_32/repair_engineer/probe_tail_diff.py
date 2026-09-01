# -*- coding: utf-8 -*-
"""Compare orig vs decompiled for the two ptradeAccount functions, dump full diffs."""
import os
import sys
import marshal
import types
import py_compile
import dis

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
import pycdc

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"
REPAIR = r"F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_32\repair_engineer"


def load_code(p):
    with open(p, "rb") as f:
        f.read(16)
        return marshal.load(f)


def find(co, name):
    if (co.co_name or "<module>") == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find(c, name)
            if r:
                return r
    return None


def instrs(co):
    return [i for i in dis.get_instructions(co) if i.opname not in ("RESUME", "CACHE")]


def fmt(i):
    a = i.argval
    if isinstance(a, types.CodeType):
        a = "<code %s>" % a.co_name
    return "%d:%-28s %r" % (i.offset, i.opname, a)


def diff_lists(oi, di):
    n = max(len(oi), len(di))
    out = []
    for k in range(n):
        o = oi[k] if k < len(oi) else None
        d = di[k] if k < len(di) else None
        so = fmt(o) if o else "<END>"
        sd = fmt(d) if d else "<END>"
        same = (o is not None and d is not None
                and o.opname == d.opname and o.argval == d.argval)
        out.append((k, so, sd, same))
    return out


src = pycdc.decompile_pyc(PYC, use_cfg=True)
ok_py = os.path.join(REPAIR, "ptradeAccount_tailOK.py")
with open(ok_py, "w", encoding="utf-8") as f:
    f.write(src)
orig = load_code(PYC)
cfile = py_compile.compile(ok_py, doraise=True, quiet=2)
dec = load_code(cfile)

for name in ("order_response_order_update", "trade_response_order_update"):
    o = find(orig, name)
    d = find(dec, name)
    print("=" * 90)
    print("FUNC", name, "orig=%d decomp=%d" % (len(instrs(o)), len(instrs(d))))
    print("-" * 90)
    rows = diff_lists(instrs(o), instrs(d))
    # print only first mismatching region and tail
    diffs = [r for r in rows if not r[3]]
    if diffs:
        lo = min(r[0] for r in diffs) - 4
        hi = max(r[0] for r in diffs) + 4
        for r in rows:
            if lo <= r[0] <= hi:
                mark = " " if r[3] else "*"
                print("%s%3d O | %s" % (mark, r[0], r[1]))
                print("%s%3d D | %s" % (mark, r[0], r[2]))
