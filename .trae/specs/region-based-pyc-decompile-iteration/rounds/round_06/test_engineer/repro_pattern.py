import sys, dis, types, marshal, os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from pycdc import decompile_pyc

CASES = {
    "default_override_isnotnone": (
        "def f(driver, dialect):\n"
        "    agreement = dialect\n"
        "    if driver is not None:\n"
        "        agreement = dialect + driver\n"
        "    return agreement\n"
    ),
    "default_override_in": (
        "def f(c, keys):\n"
        "    out = ''\n"
        "    if c in keys:\n"
        "        out = c\n"
        "    return out\n"
    ),
    "if_in_then_continue_for": (
        "def f(input_str, keys):\n"
        "    res = ''\n"
        "    for c in input_str:\n"
        "        if c in keys:\n"
        "            res = res + c\n"
        "            continue\n"
        "    return res\n"
    ),
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
    fn = "r6p_%s.py" % name
    co = compile(src, fn, "exec")
    pyc = fn + "c"
    with open(pyc, "wb") as f:
        f.write(importlib.util.MAGIC_NUMBER)
        f.write(b"\x00\x00\x00\x00")
        f.write(b"\x00" * 8)
        marshal.dump(co, f)
    dsrc = decompile_pyc(pyc, use_cfg=True)
    rco = compile(dsrc, "<d>", "exec")
    oc = []; collect(co, oc); rc = []; collect(rco, rc)
    ocf = next((c for c in oc if c.co_name == "f"), None)
    rcf = next((c for c in rc if c.co_name == "f"), None)
    sa = seq(ocf) if ocf else []; sb = seq(rcf) if rcf else []
    status = "BYTE-IDENTICAL" if sa == sb else "DIFF"
    print("==== %s : %s ====" % (name, status))
    if sa != sb:
        for i in range(max(len(sa), len(sb))):
            a = sa[i] if i < len(sa) else None
            b = sb[i] if i < len(sb) else None
            if a != b:
                print("   %3d A:%s B:%s" % (i, a, b))
    # show decompiled f
    for ln in dsrc.splitlines():
        if "def f" in ln:
            print("   DEC>", ln)
    os.remove(fn); os.remove(pyc)
