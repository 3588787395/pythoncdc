# -*- coding: utf-8 -*-
"""module_root 最小复现第四轮（只读 core/，只写 _scratch_r5v5/）。"""
import os
import subprocess
import sys

ROOT = r'f:\Downloads\pythoncdc-main'
D = os.path.dirname(os.path.abspath(__file__))

variants = {
    'y1_dotted_tuple': 'import os.path\nXX, YY = 1, 2\n',
    'y2_dotted_chained': 'import os.path\nXX = YY = 1\n',
    'y3_tuple_only': 'XX, YY = 1, 2\n',
    'y4_dotted_tuple_tail': 'import os.path\nXX, YY = 1, 2\nZZ = 3\n',
    'y5_plain_import_tuple': 'import os\nXX, YY = 1, 2\n',
    'y6_aliased_dotted_tuple': 'import os.path as p\nXX, YY = 1, 2\n',
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