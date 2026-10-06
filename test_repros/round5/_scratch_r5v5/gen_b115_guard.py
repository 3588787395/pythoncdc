# -*- coding: utf-8 -*-
"""B115 guard-safety 变体（只读 core/，只写 _scratch_r5v5/）。"""
import os
import subprocess
import sys

ROOT = r'f:\Downloads\pythoncdc-main'
D = os.path.dirname(os.path.abspath(__file__))

variants = {
    'g1_while_and': 'def f(i, j):\n    while i > 0 and j > 0:\n        i -= 1\n    return i\n',
    'g2_while_and3': 'def f(i, j, k):\n    while i > 0 and j > 0 and k > 0:\n        i -= 1\n    return i\n',
    'g3_if_and': 'def f(i, j):\n    if i > 0 and j > 0:\n        i -= 1\n    return i\n',
    'g4_if_while_and': 'def f(i, j, k):\n    if i:\n        while j > 0 and k > 0:\n            j -= 1\n    return i\n',
    'g5_if_then_while': 'def f(i):\n    if i:\n        while i > 0:\n            i -= 1\n    return i\n',
    'g6_if_if_while': 'def f(i, j):\n    if i:\n        if j:\n            while i > 0:\n                i -= 1\n    return i\n',
    'g7_while_or': 'def f(i, j):\n    while i > 0 or j > 0:\n        i -= 1\n    return i\n',
}

for name, src in variants.items():
    p = os.path.join(D, name + '.py')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(src)
    pyc = p[:-3] + '.pyc'
    subprocess.run([sys.executable, '-c',
                    'import py_compile,sys;py_compile.compile(sys.argv[1],sys.argv[2],doraise=True,optimize=0)',
                    p, pyc])
    subprocess.run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', p[:-3] + 'OK.py'])
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'), 'single', pyc],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = (r.stdout or '') + (r.stderr or '')
    tail = [l.strip() for l in out.splitlines() if 'status=' in l or 'Failure' in l]
    print('==', name)
    for t in tail:
        print('   ', t)