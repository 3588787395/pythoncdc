# -*- coding: utf-8 -*-
"""B114 残余最小化（只写 _scratch_r5v5/）。"""
import os, subprocess, sys
ROOT = r'f:\Downloads\pythoncdc-main'
D = os.path.dirname(os.path.abspath(__file__))
variants = {
    't1_doc_dotted_tuple': '"d"\nimport os.path\nXX, YY = 1, 2\n',
    't2_alias_dotted_tuple': 'import os as _os\nimport os.path\nXX, YY = 1, 2\n',
    't3_doc_alias_dotted_tuple': '"d"\nimport os as _os\nimport os.path\nXX, YY = 1, 2\n',
    't4_alias_dotted_ann_tuple': 'import os as _os\nimport os.path\nB: int = 5\nXX, YY = 1, 2\n',
    't5_doc_alias_dotted_ann_tuple': '"d"\nimport os as _os\nimport os.path\nA = 3\nB: int = 5\nXX, YY = 1, 2\n',
}
for name, src in variants.items():
    p = os.path.join(D, name + '.py')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(src)
    pyc = p[:-3] + '.pyc'
    subprocess.run([sys.executable, '-c',
                    'import py_compile,sys;py_compile.compile(sys.argv[1],sys.argv[2],doraise=True,optimize=0)',
                    p, pyc])
    subprocess.run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', p[:-3] + 'OK.py'],
                   capture_output=True, text=True)
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'), 'single', pyc],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = (r.stdout or '') + (r.stderr or '')
    tail = [l.strip() for l in out.splitlines() if 'status=' in l or 'Failure' in l]
    print('==', name)
    for t in tail:
        print('   ', t)