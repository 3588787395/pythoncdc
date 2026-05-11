import sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc
import py_compile

src_code = """try:
    pass
except ValueError:
    pass
finally:
    pass"""

tf = '_test_te05.py'
with open(tf, 'w') as f:
    f.write(src_code)

pyc = tf + 'c'
py_compile.compile(tf, cfile=pyc, doraise=True)
result = decompile_pyc(pyc)
print("Decompiled:")
print(result)

from dis import get_instructions
with open(tf) as f:
    oc = compile(f.read(), tf, 'exec')
dc = compile(result, '<d>', 'exec')

def norm(code_obj):
    return tuple(i.opname for i in get_instructions(code_obj) if not i.opname.startswith('CACHE'))

on = norm(oc)
dn = norm(dc)
print(f"\nOriginal ({len(on)}): {on}")
print(f"Decompiled ({len(dn)}): {dn}")

if os.path.exists(tf): os.remove(tf)
if os.path.exists(pyc): os.remove(pyc)
