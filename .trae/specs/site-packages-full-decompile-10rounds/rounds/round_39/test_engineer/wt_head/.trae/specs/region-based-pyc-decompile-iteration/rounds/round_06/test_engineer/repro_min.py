"""最小 G6 复现：测试当前 decompiler 对 if/while x is not None / is None 的处理。"""
import sys, dis, types, marshal, os

sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from pycdc import decompile_pyc

CASES = {
    "if_not_none": "def f(x):\n    if x is not None:\n        return x\n    return 0\n",
    "if_none": "def f(x):\n    if x is None:\n        return 0\n    return x\n",
    "while_not_none": "def f(x):\n    while x is not None:\n        x = g(x)\n    return x\n",
    "while_none": "def f(x):\n    while x is None:\n        x = g(x)\n    return x\n",
    "if_not_none_else": "def f(x):\n    if x is not None:\n        a = x\n    else:\n        a = 0\n    return a\n",
    "while_not_none_early": "def f(head):\n    while head is not None:\n        head = head.next\n    return head\n",
}

def collect(co, out):
    out.append(co)
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)

def seq(co):
    out = []
    for i in dis.get_instructions(co):
        if i.opname.startswith("JUMP") or i.opname.startswith("POP_JUMP"):
            out.append((i.opname, "<J>"))
        else:
            out.append((i.opname, i.argval))
    return out

for name, src in CASES.items():
    fn = "r6_%s.py" % name
    with open(fn, "w") as f:
        f.write(src)
    # compile to pyc
    co = compile(src, fn, "exec")
    pyc = fn + "c"
    with open(pyc, "wb") as f:
        f.write(b"\xcb\x0d\x0d\x0a" + b"\x00"*12)  # magic a70d0d0a placeholder, rewrite below
    # proper header for 3.11: magic + bit_field + 2 timestamps? Actually use importlib
    import importlib.util
    with open(pyc, "wb") as f:
        f.write(importlib.util.MAGIC_NUMBER)
        f.write(b"\x00\x00\x00\x00")  # flags
        f.write(b"\x00"*8)  # timestamps
        marshal.dump(co, f)
    # decompile
    dsrc = decompile_pyc(pyc, use_cfg=True)
    # recompile decompiled and compare sequences
    rco = compile(dsrc, "<d>", "exec")
    oc=[]; collect(co, oc); rc=[]; collect(rco, rc)
    # compare top-level f
    def find(name, lst):
        for c in lst:
            if c.co_name == name:
                return c
        return None
    ocf = find("f", oc); rcf = find("f", rc)
    sa = seq(ocf) if ocf else []; sb = seq(rcf) if rcf else []
    status = "BYTE-IDENTICAL" if sa == sb else "DIFF"
    print("==== %s : %s ====" % (name, status))
    if sa != sb:
        for i in range(max(len(sa),len(sb))):
            a = sa[i] if i<len(sa) else None
            b = sb[i] if i<len(sb) else None
            if a!=b:
                print("   %3d A:%s B:%s" % (i,a,b))
    # show decompiled f
    for ln in dsrc.splitlines():
        if "def f" in ln:
            print("   DEC>", ln)
    os.remove(fn); os.remove(pyc)
