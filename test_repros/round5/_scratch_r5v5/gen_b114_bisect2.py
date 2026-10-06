# -*- coding: utf-8 -*-
"""B114 全量二分 2（只写 _scratch_r5v5/）。"""
import os, subprocess, sys
ROOT = r'f:\Downloads\pythoncdc-main'
D = os.path.dirname(os.path.abspath(__file__))
HEAD = '"""docstring."""\nimport os as _os\nimport os.path\n\n'

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

A = 'MOD_A = 3\n'
B = 'MOD_B: int = 5\n'
C = 'MOD_C, MOD_D = 1, 2\n'
D2 = 'MOD_E = MOD_F = 9\n'
E = 'MOD_G = MOD_A if MOD_A > 0 else MOD_B\n'
run('q1_ab', HEAD + A + B)
run('q2_abc', HEAD + A + B + C)
run('q3_abcd', HEAD + A + B + C + D2)
run('q4_abce', HEAD + A + B + C + E)
run('q5_bc', HEAD + B + C)
run('q6_ac', HEAD + A + C)
run('q7_c_only', HEAD + C)
run('q8_ab_cd', HEAD + A + B + C + D2)