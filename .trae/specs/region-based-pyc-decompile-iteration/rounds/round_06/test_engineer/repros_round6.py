import sys, dis, types, marshal, os, importlib.util
sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from pycdc import decompile_pyc
HERE = os.path.dirname(os.path.abspath(__file__))

def collect(co, out):
    out.append(co)
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)

def seq(co):
    return [((i.opname, "<J>") if i.opname.startswith(("JUMP", "POP_JUMP")) else (i.opname, i.argval)) for i in dis.get_instructions(co)]

def check(name, src, fnname):
    fn = os.path.join(HERE, "r6_tmp_%s.py" % name)
    co = compile(src, fn, "exec"); pyc = fn + "c"
    with open(pyc, "wb") as f:
        f.write(importlib.util.MAGIC_NUMBER); f.write(b"\x00" * 12); marshal.dump(co, f)
    dsrc = decompile_pyc(pyc, use_cfg=True)
    rco = compile(dsrc, "<d>", "exec")
    oc = []; collect(co, oc); rc = []; collect(rco, rc)
    ocf = next((c for c in oc if c.co_name == fnname), None)
    rcf = next((c for c in rc if c.co_name == fnname), None)
    sa = seq(ocf); sb = seq(rcf)
    status = "BYTE-IDENTICAL" if sa == sb else "DIFF"
    print("==== %s: %s" % (name, status))
    if sa != sb:
        for i in range(max(len(sa), len(sb))):
            a = sa[i] if i < len(sa) else None; b = sb[i] if i < len(sb) else None
            if a != b:
                print("  %3d A:%s B:%s" % (i, a, b))
    for ln in dsrc.splitlines():
        if "if " in ln or "while " in ln or "is None" in ln or "is not None" in ln or ("def " + fnname) in ln:
            print("  DEC>", ln)
    try: os.remove(fn); os.remove(pyc)
    except Exception: pass

DEFAULT = "DB = {}"
# 1. the bug: or-assignment + if is not None + else
check("parsedb",
    "DB = {}\n"
    "def f(config):\n"
    "    dialect = config.pop('dialect', 'mysql')\n"
    "    driver = config.pop('driver', None) or DB.get(dialect)\n"
    "    if driver is not None:\n"
    "        a = '{}+{}'.format(dialect, driver)\n"
    "    else:\n"
    "        a = dialect\n"
    "    return a\n", "f")

# 2. positive is None + or-assignment + else
check("isnone",
    "DB = {}\n"
    "def f(config):\n"
    "    driver = config.pop('driver', None) or DB.get('x')\n"
    "    if driver is None:\n"
    "        a = 'none'\n"
    "    else:\n"
    "        a = driver\n"
    "    return a\n", "f")

# 3. or-assignment + if is not None, NO else
check("nonone_no_else",
    "DB = {}\n"
    "def f(config):\n"
    "    driver = config.pop('driver', None) or DB.get('x')\n"
    "    if driver is not None:\n"
    "        a = driver\n"
    "    return a\n", "f")

# 4. simple if is not None (no or) — baseline must stay identical
check("simple_nonone",
    "def f(x):\n"
    "    if x is not None:\n"
    "        a = x\n"
    "    else:\n"
    "        a = 0\n"
    "    return a\n", "f")

# 5. simple if is None (no or)
check("simple_isnone",
    "def f(x):\n"
    "    if x is None:\n"
    "        a = 0\n"
    "    else:\n"
    "        a = x\n"
    "    return a\n", "f")

# 6. while is not None + or-assignment
check("while_nonone",
    "DB = {}\n"
    "def f(config):\n"
    "    driver = config.pop('driver', None) or DB.get('x')\n"
    "    while driver is not None:\n"
    "        driver = None\n"
    "    return driver\n", "f")

# 7. inline if after or (no else) — must not crash / must be sane
check("inline_after_or",
    "DB = {}\n"
    "def f(config):\n"
    "    driver = config.pop('driver', None) or DB.get('x')\n"
    "    if driver is not None:\n"
    "        a = driver\n"
    "    return a\n", "f")
