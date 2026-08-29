import sys, dis, types, marshal, os, importlib.util
sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from pycdc import decompile_pyc

HERE = os.path.dirname(os.path.abspath(__file__))

SRC = (
    "CHN_DIGIT_MAP = {}\n"
    "SCORE_FEATURE_STR = set()\n"
    "DECIMAL_FEATURE_STR = set()\n"
    "def getchnstr(input_str):\n"
    "    chn_str = ''\n"
    "    for c in input_str:\n"
    "        if c in CHN_DIGIT_MAP.keys():\n"
    "            if c in SCORE_FEATURE_STR or c in DECIMAL_FEATURE_STR:\n"
    "                chn_str = chn_str + c\n"
    "                continue\n"
    "            elif len(chn_str) > 0:\n"
    "                break\n"
    "            else:\n"
    "                continue\n"
    "    return chn_str\n"
)

def collect(co, out):
    out.append(co)
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)

def seq(co):
    return [((i.opname, "<J>") if i.opname.startswith(("JUMP", "POP_JUMP")) else (i.opname, i.argval)) for i in dis.get_instructions(co)]

fn = os.path.join(HERE, "r6_getchnstr.py")
co = compile(SRC, fn, "exec"); pyc = fn + "c"
with open(pyc, "wb") as f:
    f.write(importlib.util.MAGIC_NUMBER); f.write(b"\x00" * 12); marshal.dump(co, f)
dsrc = decompile_pyc(pyc, use_cfg=True)
rco = compile(dsrc, "<d>", "exec")
oc = []; collect(co, oc); rc = []; collect(rco, rc)
ocf = next((c for c in oc if c.co_name == "getchnstr"), None)
rcf = next((c for c in rc if c.co_name == "getchnstr"), None)
sa = seq(ocf); sb = seq(rcf)
print("==== getchnstr faithful repro:", "BYTE-IDENTICAL" if sa == sb else "DIFF")
if sa != sb:
    for i in range(max(len(sa), len(sb))):
        a = sa[i] if i < len(sa) else None; b = sb[i] if i < len(sb) else None
        if a != b:
            print("  %3d A:%s B:%s" % (i, a, b))
for ln in dsrc.splitlines():
    if "def getchnstr" in ln or "in CHN" in ln or "not" in ln:
        print("  DEC>", ln)
try:
    os.remove(fn); os.remove(pyc)
except Exception as e:
    print("cleanup", e)
