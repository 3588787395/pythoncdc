import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
os.chdir(r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1')
from pycdc import decompile_pyc
from dis import get_instructions

def norm(code_obj):
    return tuple(i.opname for i in get_instructions(code_obj) if not i.opname.startswith('CACHE'))

for tf in ['test_r1_with_as.py','test_r1_with_no_as.py','test_r1_multi_with.py','test_r1_nested_with.py','test_r1_with_try.py']:
    pyc = tf+'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    src = decompile_pyc(pyc)
    with open(tf) as f:
        oc = compile(f.read(), tf, 'exec')
    try:
        dc = compile(src, '<d>', 'exec')
        on = norm(oc.co_consts[0])
        dn = norm(dc.co_consts[0])
        status = "MATCH" if on == dn else "DIFF"
        print(f'{tf}: {status}')
    except Exception as e:
        print(f'{tf}: COMPILE ERROR: {e}')
    if os.path.exists(pyc):
        os.remove(pyc)
