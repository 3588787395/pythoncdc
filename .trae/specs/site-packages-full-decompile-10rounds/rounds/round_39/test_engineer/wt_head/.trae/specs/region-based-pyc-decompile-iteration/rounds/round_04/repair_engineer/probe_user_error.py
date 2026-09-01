import sys, dis, marshal
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from pycdc import decompile_pyc

PATH = r"F:\Downloads\pythoncdc-main\site-packages\fly\common\user_error.pyc"
src = decompile_pyc(PATH)
print("=== decompiled user_error.pyc (head) ===")
print(src[:1800])

with open(PATH, "rb") as f:
    f.read(16)
    code = marshal.load(f)
print("\n=== ORIG <module> full dis ===")
dis.dis(code)
PY
