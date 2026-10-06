# -*- coding: utf-8 -*-
"""生成 module_root 最小化变体并运行 verify（只读 core/，只写 _scratch_r5v5/）。"""
import os
import subprocess
import sys

ROOT = r'f:\Downloads\pythoncdc-main'
D = os.path.dirname(os.path.abspath(__file__))

variants = {
    'v_doc_only': '"doc"\nimport os.path\n',
    'v_doc_pair': '"doc"\nimport os as _os\nimport os.path\n',
    'v_pair_body': 'import os as _os\nimport os.path\nMOD_A = 3\nMOD_B: int = 5\n',
    'v_doc_pair_body': '"doc"\nimport os as _os\nimport os.path\nMOD_A = 3\nMOD_B: int = 5\nMOD_C, MOD_D = 1, 2\n',
    'v_pair_dunder': 'import os as _os\nimport os.path\nif __name__ == "__main__":\n    X = 1\n',
    'v_pair_loop_else': 'import os as _os\nimport os.path\nfor i in range(2):\n    pass\nelse:\n    Y = 1\n',
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