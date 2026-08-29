"""检查单个 pyc 的指定函数：打印原始字节码 + 反编译源码中该函数片段。"""
import sys, dis, types, marshal, re

sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from pycdc import decompile_pyc

pyc = sys.argv[1]
func = sys.argv[2] if len(sys.argv) > 2 else None

with open(pyc, "rb") as f:
    f.read(16)
    omc = marshal.load(f)


def collect(co, out):
    out.append(co)
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)


oc = []
collect(omc, oc)

print("===== ORIGINAL BYTECODE: %s =====" % func)
for co in oc:
    if co.co_name != func:
        continue
    for i in dis.get_instructions(co):
        print("  %3d %-32s %s" % (i.offset, i.opname, i.argval))
    break

src = decompile_pyc(pyc, use_cfg=True)
print("\n===== DECOMPILED SOURCE (parse_db_url region) =====")
lines = src.splitlines()
capture = False
depth = 0
for ln in lines:
    if func and ("def %s" % func) in ln:
        capture = True
    if capture:
        print(ln)
        if ln.strip().startswith("def "):
            depth = ln.count("    ") if False else 0
    if capture and ln.strip() == "" and False:
        pass
# simpler: just grep the function block
print("\n===== raw grep def %s =====" % func)
for j, ln in enumerate(lines):
    if ("def %s" % func) in ln:
        for k in range(j, min(j + 60, len(lines))):
            print(lines[k])
            if k > j and lines[k].startswith("def ") and k != j:
                break
        break
