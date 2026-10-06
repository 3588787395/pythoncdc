# -*- coding: utf-8 -*-
"""module_root 交叉最小化第二轮（只读 core/，只写 _scratch_r5v5/）。"""
import os
import subprocess
import sys

ROOT = r'f:\Downloads\pythoncdc-main'
D = os.path.dirname(os.path.abspath(__file__))

variants = {
    'w1_doc_pair_a': '"doc"\nimport os as _os\nimport os.path\nMOD_A = 3\n',
    'w2_doc_pair_bann': '"doc"\nimport os as _os\nimport os.path\nMOD_B: int = 5\n',
    'w3_doc_pair_b': '"doc"\nimport os as _os\nimport os.path\nMOD_B = 5\n',
    'w4_doc_pair_ab': '"doc"\nimport os as _os\nimport os.path\nMOD_A = 3\nMOD_B = 5\n',
    'w5_doc_dotted_ann': '"doc"\nimport os.path\nX: int = 5\n',
    'w6_nodoc_pair_a_ann': 'import os as _os\nimport os.path\nMOD_A = 3\nMOD_B: int = 5\n',
    'w7_doc_alias_dotted_ann': '"doc"\nimport os as _os\nimport os.path\nQ: int = 5\n',
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