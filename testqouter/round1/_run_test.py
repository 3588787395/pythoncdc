import py_compile, sys, os

os.chdir(r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1')
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc

for tf in ['test_r1_if_for_break.py', 'test_r1_if_while_break.py', 'test_r1_for_if_for_break.py', 'test_r1_while_and_condition.py']:
    pyc = tf + 'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    try:
        src = decompile_pyc(pyc)
        print(f'=== {tf} ===')
        print(src)
        print()
    except Exception as e:
        print(f'=== {tf} === ERROR: {e}')
        import traceback; traceback.print_exc()
        print()
    if os.path.exists(pyc): os.remove(pyc)
