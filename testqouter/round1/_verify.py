import py_compile, sys, os
os.chdir(r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1')
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc
from dis import get_instructions

def norm(code_obj):
    return tuple(i.opname for i in get_instructions(code_obj) if not i.opname.startswith('CACHE'))

for tf in ['test_r1_if_for_break.py', 'test_r1_if_while_break.py', 'test_r1_for_if_for_break.py', 'test_r1_while_and_condition.py']:
    pyc = tf+'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    src = decompile_pyc(pyc)
    with open(tf) as f:
        oc = compile(f.read(), tf, 'exec')
    dc = compile(src, '<d>', 'exec')
    on = norm(oc.co_consts[0])
    dn = norm(dc.co_consts[0])
    print(f'{tf}: {"MATCH" if on==dn else "DIFF"}')
    if on != dn:
        print(src)
        print('Original:', on)
        print('Decompiled:', dn)
    if os.path.exists(pyc): os.remove(pyc)
