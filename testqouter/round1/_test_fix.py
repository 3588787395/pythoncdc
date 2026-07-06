import sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc
import py_compile
from dis import get_instructions

def norm(code_obj):
    return tuple((i.opname, i.argval) for i in get_instructions(code_obj) if not i.opname.startswith('CACHE'))

for tf in ['test_e05_try_except_finally.py','test_e09_nested_try.py','test_e12_try_with_if.py']:
    pyc = tf + 'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    src = decompile_pyc(pyc)
    with open(tf) as f:
        oc = compile(f.read(), tf, 'exec')
    dc = compile(src, '<d>', 'exec')
    on = norm(oc.co_consts[0])
    dn = norm(dc.co_consts[0])
    match = "MATCH" if on == dn else "DIFF"
    print(f'=== {tf}: {match} ===')
    if on != dn:
        print("  ORIG:")
        for i, o in enumerate(on):
            print(f"    [{i}] {o}")
        print("  DECOMPILED:")
        for i, d in enumerate(dn):
            print(f"    [{i}] {d}")
    if os.path.exists(pyc):
        os.remove(pyc)
