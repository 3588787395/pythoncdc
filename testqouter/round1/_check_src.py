import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc

for tf in ['test_e03_try_else_finally.py','test_e05_try_except_finally.py','test_r1_try_except_finally.py']:
    pyc = tf+'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    src = decompile_pyc(pyc)
    print(f'=== {tf} ===')
    print(repr(src))
    print()
    if os.path.exists(pyc): os.remove(pyc)
