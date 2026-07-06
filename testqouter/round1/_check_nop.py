import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc
from dis import get_instructions

def norm(code_obj):
    return tuple(i.opname for i in get_instructions(code_obj) if not i.opname.startswith('CACHE'))

for tf in ['test_e03_try_else_finally.py','test_e05_try_except_finally.py','test_e06_full_combination.py','test_r1_try_except_else_finally.py','test_r1_try_except_finally.py']:
    if not os.path.exists(tf):
        print(f'{tf}: FILE NOT FOUND')
        continue
    pyc = tf+'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    src = decompile_pyc(pyc)
    with open(tf) as f:
        oc = compile(f.read(), tf, 'exec')
    dc = compile(src, '<d>', 'exec')
    on = norm(oc.co_consts[0])
    dn = norm(dc.co_consts[0])
    match = "MATCH" if on==dn else "DIFF"
    print(f'{tf}: {match} (orig={len(on)} deco={len(dn)})')
    if on != dn:
        for i, (a, b) in enumerate(zip(on, dn)):
            if a != b:
                print(f'  pos {i}: orig={a} deco={b}')
                if i > 5:
                    print(f'  ... (showing first 6 differences)')
                    break
        if len(on) != len(dn):
            print(f'  length diff: orig has {len(on)}, deco has {len(dn)}')
    if os.path.exists(pyc): os.remove(pyc)
