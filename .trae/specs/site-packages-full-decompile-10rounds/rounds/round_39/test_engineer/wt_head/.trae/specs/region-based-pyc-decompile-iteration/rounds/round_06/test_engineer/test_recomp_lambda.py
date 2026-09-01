import sys, dis, types, marshal
sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from pycdc import decompile_pyc

pyc = "./site-packages/IQData/modules/WEBCLIENT/web_socket_client.pyc"
src = decompile_pyc(pyc, use_cfg=True)
rmc = compile(src, "<d>", "exec")

def walk(co, depth=0):
    for cc in co.co_consts:
        if isinstance(cc, types.CodeType):
            if cc.co_name == "<lambda>":
                lcs = [i.argval for i in dis.get_instructions(cc) if i.opname == "LOAD_CONST"]
                print("  lambda consts:", cc.co_consts, "LOAD_CONSTs:", lcs)
            walk(cc, depth + 1)

print("=== RECOMPILED decompiled source lambdas ===")
walk(rmc)

with open(pyc, "rb") as f:
    f.read(16)
    omc = marshal.load(f)
print("=== ORIGINAL pyc lambdas ===")
walk(omc)
