# -*- coding: utf-8 -*-
"""if+while 融合 / 裸注解 最小复现（只读 core/，只写 _scratch_r5v5/）。"""
import os
import subprocess
import sys

ROOT = r'f:\Downloads\pythoncdc-main'
D = os.path.dirname(os.path.abspath(__file__))

variants = {
    'k1_ifwhile': 'def f(i):\n    if i:\n        while i > 0:\n            i -= 1\n    return i\n',
    'k2_ifwhile_flag': 'def f(flag, i):\n    if flag:\n        while i > 0:\n            i -= 1\n    return i\n',
    'k3_ifwhile_swap': 'def f(i):\n    while i > 0:\n        if i:\n            i -= 1\n    return i\n',
    'k4_bare_ann': 'def f():\n    b: str\n    return b\n',
    'k5_bare_ann_assign': 'def f(x):\n    b: str\n    b = x\n    return b\n',
    'k6_ann_only': 'def f():\n    b: int = 3\n    return b\n',
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