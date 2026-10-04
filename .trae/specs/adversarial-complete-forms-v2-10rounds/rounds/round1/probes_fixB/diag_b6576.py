"""B65/B76 最小复现：生成探针 pyc + region 反编译，确认 UnboundLocalError/目标丢失"""
import sys, io, os, py_compile

BASE = r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB"
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")

SRC = '''\
def chain3_boolop(x, y):
    a = b = c = (x > 0 and y > 0)
    return a + b + c

def chain2_boolop(x, y):
    a = b = (x > 0 and y > 0)
    return a + b

def aug_boolop(x, a, b):
    x += a and b
    return x
'''
src_path = os.path.join(BASE, "b6576_probe.py")
with open(src_path, "w", encoding="utf-8") as f:
    f.write(SRC)
pyc_path = os.path.join(BASE, "b6576_probe.pyc")
py_compile.compile(src_path, cfile=pyc_path, doraise=True)
print("pyc written:", pyc_path)

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(pyc_path)
out = io.StringIO()
try:
    ok = dec.decompile(out, use_region=True)
    print("decompile ok:", ok)
except Exception as e:
    import traceback
    traceback.print_exc()
print("=== decompiled ===")
print(out.getvalue())
