import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
os.chdir(r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1')
from pycdc import decompile_pyc
from dis import get_instructions

def norm(code_obj):
    return tuple(i.opname for i in get_instructions(code_obj) if not i.opname.startswith('CACHE'))

for tf in ['test_w01_with.py','test_w02_with_no_as.py','test_w03_multi_with.py','test_w04_nested_with.py','test_w05_with_with_try.py','test_w06_try_with_with.py']:
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
        if on != dn:
            for i, (a, b) in enumerate(zip(on, dn)):
                if a != b:
                    print(f'  diff at {i}: orig={a} decomp={b}')
            if len(on) != len(dn):
                print(f'  length diff: orig={len(on)} decomp={len(dn)}')
    except Exception as e:
        print(f'{tf}: COMPILE ERROR: {e}')
    if os.path.exists(pyc):
        os.remove(pyc)
