import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc
from dis import get_instructions

def norm(code_obj):
    return tuple(i.opname for i in get_instructions(code_obj) if not i.opname.startswith('CACHE'))

tf = 'test_e09_nested_try.py'
pyc = tf + 'c'
py_compile.compile(tf, cfile=pyc, doraise=True)
src = decompile_pyc(pyc)
with open(tf) as f:
    oc = compile(f.read(), tf, 'exec')
dc = compile(src, '<d>', 'exec')
on = norm(oc.co_consts[0])
dn = norm(dc.co_consts[0])
print("Original (%d): %s" % (len(on), on))
print("Decompiled (%d): %s" % (len(dn), dn))
print()
print("Decompiled source:")
print(src)
if os.path.exists(pyc):
    os.remove(pyc)
