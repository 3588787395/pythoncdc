import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc
from dis import get_instructions

def norm(code_obj):
    return tuple(i.opname for i in get_instructions(code_obj) if not i.opname.startswith('CACHE'))

tests = ['test_e05_try_except_finally.py','test_e09_nested_try.py','test_e11_loop_with_try.py','test_e12_try_with_if.py','test_n12_for_try_except.py','test_n16_for_if_try_except.py','test_r1_for_if_try_except.py','test_r1_for_try_except.py','test_r1_if_try_except.py','test_r1_for_nested_try_break.py','test_n11_try_while_continue.py']
match = 0
for tf in tests:
    pyc = tf+'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    src = decompile_pyc(pyc)
    with open(tf) as f:
        oc = compile(f.read(), tf, 'exec')
    dc = compile(src, '<d>', 'exec')
    on = norm(oc.co_consts[0])
    dn = norm(dc.co_consts[0])
    m = 'MATCH' if on==dn else 'DIFF'
    if on==dn: match += 1
    print(f'{tf}: {m}')
    if m == 'DIFF':
        print(f'  ORIG: {on}')
        print(f'  DECO: {dn}')
        print(f'  SRC: {src}')
    if os.path.exists(pyc): os.remove(pyc)
print(f'\nTotal: {match}/{len(tests)} matched')
