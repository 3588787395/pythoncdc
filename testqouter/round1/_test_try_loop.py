import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc
from dis import get_instructions

def norm(code_obj):
    return tuple(i.opname for i in get_instructions(code_obj) if not i.opname.startswith('CACHE'))

for tf in ['test_e11_loop_with_try.py','test_r1_for_try_except.py','test_n12_for_try_except.py','test_r1_for_nested_try_break.py']:
    pyc = tf+'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    src = decompile_pyc(pyc)
    with open(tf) as f:
        oc = compile(f.read(), tf, 'exec')
    dc = compile(src, '<d>', 'exec')
    on = norm(oc.co_consts[0])
    dn = norm(dc.co_consts[0])
    print(f'=== {tf} ===')
    print(f'Result: {"MATCH" if on==dn else "DIFF"}')
    print('Decompiled source:')
    print(src)
    if on != dn:
        print('ORIG:', on)
        print('DECO:', dn)
        for idx, (o, d) in enumerate(zip(on, dn)):
            if o != d:
                print(f'  First diff at index {idx}: orig={o}, deco={d}')
                break
    print()
    if os.path.exists(pyc): os.remove(pyc)
