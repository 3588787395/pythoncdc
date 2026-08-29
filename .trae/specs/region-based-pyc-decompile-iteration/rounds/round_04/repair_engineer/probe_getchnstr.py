import sys, dis, marshal
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from pycdc import decompile_pyc

PATH = r"F:\Downloads\pythoncdc-main\site-packages\fly\common\convert.pyc"
src = decompile_pyc(PATH)
idx = src.find("def getchnstr")
print("=== decompiled getchnstr ===")
print(src[idx:idx+900])

# orig bytecode of getchnstr
with open(PATH,"rb") as f:
    f.read(16); code=marshal.load(f)
def walk(co):
    if co.co_name=='getchnstr':
        print("\n=== ORIG getchnstr ===")
        dis.dis(co)
        print("co_names", co.co_names, "co_varnames", co.co_varnames, "co_consts", co.co_consts)
    for c in co.co_consts:
        if hasattr(c,'co_code'): walk(c)
walk(code)
