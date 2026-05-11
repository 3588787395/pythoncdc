import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc
from dis import get_instructions

def norm(code_obj):
    return tuple((i.opname, i.argval) for i in get_instructions(code_obj) if not i.opname.startswith('CACHE'))

for tf in ['test_r1_try_except_finally.py']:
    pyc = tf+'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    src = decompile_pyc(pyc)
    with open(tf) as f:
        oc = compile(f.read(), tf, 'exec')
    dc = compile(src, '<d>', 'exec')
    on = norm(oc.co_consts[0])
    dn = norm(dc.co_consts[0])
    print(f'=== {tf} ===')
    print(f'Original ({len(on)}):')
    for i, (op, val) in enumerate(on):
        print(f'  {i:3d}: {op:30s} {val!r}')
    print(f'Decompiled ({len(dn)}):')
    for i, (op, val) in enumerate(dn):
        print(f'  {i:3d}: {op:30s} {val!r}')
    if os.path.exists(pyc): os.remove(pyc)
