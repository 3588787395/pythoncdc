import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc

tests = ['test_e05_try_except_finally.py','test_e09_nested_try.py','test_e11_loop_with_try.py','test_e12_try_with_if.py','test_n12_for_try_except.py','test_n16_for_if_try_except.py','test_r1_for_if_try_except.py','test_r1_for_try_except.py','test_r1_if_try_except.py','test_r1_for_nested_try_break.py','test_n11_try_while_continue.py']
for tf in tests:
    pyc = tf+'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    try:
        src = decompile_pyc(pyc)
        print(f'=== {tf} ===')
        print(src)
        print()
    except Exception as e:
        print(f'=== {tf} === ERROR: {e}')
        print()
    if os.path.exists(pyc): os.remove(pyc)
