# -*- coding: utf-8 -*-
"""B114 全量二分（只写 _scratch_r5v5/）。"""
import os, subprocess, sys
ROOT = r'f:\Downloads\pythoncdc-main'
D = os.path.dirname(os.path.abspath(__file__))

HEAD = '"""docstring."""\nimport os as _os\nimport os.path\n\n'
BODY = {
 'a_assigns': 'MOD_A = 3\nMOD_B: int = 5\nMOD_C, MOD_D = 1, 2\nMOD_E = MOD_F = 9\nMOD_G = MOD_A if MOD_A > 0 else MOD_B\n',
 'b_if': "if MOD_A > 1:\n    MOD_H = 'a'\nelif MOD_A > 0:\n    MOD_H = 'b'\nelse:\n    MOD_H = 'c'\n",
 'c_for': 'for _i in range(2):\n    MOD_I = _i\nelse:\n    MOD_I = -1\n',
 'd_while': 'while MOD_D < 4:\n    MOD_D += 1\nelse:\n    MOD_D = 0\n',
 'e_comp': 'MOD_J = [v for v in range(3)]\nMOD_K = f"{MOD_A!r}"\n',
 'f_main': "if __name__ == '__main__':\n    MOD_L = MOD_A + MOD_B\n",
}

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
    ok = os.path.join(D, name + 'OK.py')
    phantom = ''
    try:
        txt = open(ok, encoding='utf-8').read()
        if 'os.path as os' in txt:
            phantom = ' PHANTOM!'
    except Exception:
        pass
    print('==', name, phantom)
    for t in st:
        print('   ', t)

# cumulative
for k in ['a_assigns', 'b_if', 'c_for', 'd_while', 'e_comp', 'f_main']:
    pass
run('z1_body_a', HEAD + BODY['a_assigns'])
run('z2_a_c', HEAD + BODY['a_assigns'] + BODY['c_for'])
run('z3_a_d', HEAD + BODY['a_assigns'] + BODY['d_while'])
run('z4_a_e', HEAD + BODY['a_assigns'] + BODY['e_comp'])
run('z5_a_f', HEAD + BODY['a_assigns'] + BODY['f_main'])
run('z6_full', HEAD + BODY['a_assigns'] + BODY['b_if'] + BODY['c_for'] + BODY['d_while'] + BODY['e_comp'] + BODY['f_main'])