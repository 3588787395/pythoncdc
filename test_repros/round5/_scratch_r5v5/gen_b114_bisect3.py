# -*- coding: utf-8 -*-
"""B114 ternary 触发最小化（只写 _scratch_r5v5/）。"""
import os, subprocess, sys
ROOT = r'f:\Downloads\pythoncdc-main'
D = os.path.dirname(os.path.abspath(__file__))

def run(name, src):
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
    st = [l.strip() for l in out.splitlines() if 'status=' in l]
    phantom = ''
    try:
        if 'os.path as os' in open(os.path.join(D, name + 'OK.py'), encoding='utf-8').read():
            phantom = ' PHANTOM!'
    except Exception:
        pass
    print('==', name, phantom)
    for t in st:
        print('   ', t)

run('r1_ce', '"""d"""\nimport os as _os\nimport os.path\nMOD_C, MOD_D = 1, 2\nMOD_G = 1 if MOD_C > 0 else 2\n')
run('r2_e', '"""d"""\nimport os as _os\nimport os.path\nMOD_G = 1 if MOD_C > 0 else 2\n')
run('r3_e_min', 'import os.path\nXX, YY = 1, 2\nG = 1 if XX > 0 else 2\n')
run('r4_e_only', 'import os.path\nG = 1 if XX > 0 else 2\n')
run('r5_tuple_if', 'import os.path\nXX, YY = 1, 2\nif XX:\n    G = 1\nelse:\n    G = 2\n')
run('r6_tuple_tern_nodoc_noalias', 'import os.path\nXX, YY = 1, 2\nG = XX if XX else 2\n')