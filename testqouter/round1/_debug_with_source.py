import sys, os, py_compile
os.chdir(r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1')
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc

for tf in ['test_w01_with.py', 'test_w02_with_no_as.py']:
    pyc = tf + 'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    src = decompile_pyc(pyc)
    lines = src.split('\n')
    clean = [l for l in lines if not l.startswith('# Source') and not l.startswith('# File:')]
    print(f'=== {tf} ===')
    print('\n'.join(clean))
    print()
    if os.path.exists(pyc):
        os.remove(pyc)
