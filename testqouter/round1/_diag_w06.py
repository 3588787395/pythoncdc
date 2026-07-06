import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
os.chdir(r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1')
from pycdc import decompile_pyc

for tf in ['test_w06_try_with_with.py']:
    pyc = tf + 'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    src = decompile_pyc(pyc)
    print(f'=== {tf} DECOMPILED ===')
    print(src)
    print()
    if os.path.exists(pyc):
        os.remove(pyc)
