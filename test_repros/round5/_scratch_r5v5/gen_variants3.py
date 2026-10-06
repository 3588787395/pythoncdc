# -*- coding: utf-8 -*-
"""module_root 交叉最小化第三轮（只读 core/，只写 _scratch_r5v5/）。"""
import os
import subprocess
import sys

ROOT = r'f:\Downloads\pythoncdc-main'
D = os.path.dirname(os.path.abspath(__file__))

P = 'import os as _os\nimport os.path\n'
variants = {
    'x1_doc_pair_tuple': '"doc"\n' + P + 'MOD_C, MOD_D = 1, 2\n',
    'x2_doc_pair_bann_tuple': '"doc"\n' + P + 'MOD_B: int = 5\nMOD_C, MOD_D = 1, 2\n',
    'x3_doc_pair_a_tuple': '"doc"\n' + P + 'MOD_A = 3\nMOD_C, MOD_D = 1, 2\n',
    'x4_doc_pair_a_bann': '"doc"\n' + P + 'MOD_A = 3\nMOD_B: int = 5\n',
    'x5_pair_full_nodoc': P + 'MOD_A = 3\nMOD_B: int = 5\nMOD_C, MOD_D = 1, 2\n',
    'x6_doc_dotted_full': '"doc"\nimport os.path\nMOD_A = 3\nMOD_B: int = 5\nMOD_C, MOD_D = 1, 2\n',
    'x7_doc_pair_rename': '"doc"\n' + P + 'A = 3\nB: int = 5\nC, D = 1, 2\n',
    'x8_doc_pair_xy_tuple': '"doc"\n' + P + 'XX, YY = 1, 2\n',
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