# -*- coding: utf-8 -*-
"""Round5 复核变体探针生成 + RV2 regen + verify（只读 core/，只写 test_repros/round5/r5v5r_*）。
前缀 r5v5r_（零覆盖既有文件）。用法：python gen_probes_r5v5r.py
"""
import json
import os
import re
import subprocess
import sys

ROOT = r'f:\Downloads\pythoncdc-main'
D = os.path.join(ROOT, 'test_repros', 'round5')
OUT = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'rounds', 'round5')
STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')

# ---- 探针源 ----
P = {}
# B114 变体
P['r5v5r_b114_module'] = 'import os.path\n'
P['r5v5r_b114_in_for'] = 'r = []\nfor i in range(3):\n    import os.path\n    r.append(os.path)\n'
P['r5v5r_b114_in_while'] = 'r = []\nn = 2\nwhile n > 0:\n    import os.path\n    r.append(os.path)\n    n -= 1\n'
P['r5v5r_b114_in_func_for'] = ('def f():\n    r = []\n    for i in range(3):\n'
                               '        import os.path\n        r.append(os.path)\n    return r\n')
P['r5v5r_b114_realias'] = 'import os.path as op\nX = op.join("a", "b")\n'
P['r5v5r_b114_from'] = 'from os import path\nY = path.join("a", "b")\n'
P['r5v5r_b114_deep3'] = 'import os.path\nZ = 1\n'
P['r5v5r_b114_tuple'] = 'import os.path\nXX, YY = 1, 2\n'
P['r5v5r_b114_multi'] = 'import os\nimport os.path\nW = 1\n'
P['r5v5r_b114_in_try'] = 'try:\n    import os.path\n    V = os.path\nfinally:\n    pass\n'
# B115 变体
P['r5v5r_b115_while_and'] = 'def f(a, b):\n    while a and b:\n        a -= 1\n    return a\n'
P['r5v5r_b115_while_or'] = 'def f(a, b):\n    while a or b:\n        a -= 1\n    return a\n'
P['r5v5r_b115_while_and3'] = 'def f(a, b, c):\n    while a and b and c:\n        a -= 1\n    return a\n'
P['r5v5r_b115_if_while'] = 'def f(i):\n    if i:\n        while i > 0:\n            i -= 1\n    return i\n'
P['r5v5r_b115_if_and_while'] = 'def f(a, b):\n    if a and b:\n        while a > 0:\n            a -= 1\n    return a\n'
P['r5v5r_b115_nested_for_while'] = ('def f(xs):\n    r = 0\n    for i in xs:\n        while i > 0:\n'
                                    '            i -= 1\n            r += i\n    return r\n')
P['r5v5r_b115_while_in_try'] = ('def f(a):\n    try:\n        while a > 0:\n            a -= 1\n'
                                '    finally:\n        pass\n    return a\n')
P['r5v5r_b115_for_if_while'] = ('def f(xs):\n    r = 0\n    for i in xs:\n        if i:\n'
                                '            while i > 0:\n                r = i\n'
                                '                i -= 1\n    return r\n')
P['r5v5r_b115_while_true_break'] = 'def f(a):\n    while a and a > 0:\n        a -= 1\n        if a < 0:\n            break\n    return a\n'
P['r5v5r_b115_while_reeval'] = ('def f(redata, count):\n    while not redata and count < 3:\n'
                                '        count += 1\n    return count\n')
# B116 变体
P['r5v5r_b116_bare'] = 'def f():\n    b: str\n    return b\n'
P['r5v5r_b116_posonly'] = 'def f(a, /):\n    return a\n'
P['r5v5r_b116_posonly_kw'] = 'def f(a, /, b):\n    return a + b\n'
P['r5v5r_b116_posonly_only'] = 'def f(a, b, /):\n    return a + b\n'
P['r5v5r_b116_kwonly'] = 'def f(*, b):\n    return b\n'
P['r5v5r_b116_class_bare'] = 'class C:\n    def m(self):\n        q: int\n        return q\n'
P['r5v5r_b116_loop_bare'] = 'def f(xs):\n    k: int\n    for x in xs:\n        k = x\n    return k\n'
P['r5v5r_b116_cond_bare'] = 'def f(x):\n    y: str\n    if x:\n        y = "a"\n    return y\n'
P['r5v5r_b116_closure_bare'] = ('def f():\n    z: int\n    def g():\n        return z\n'
                                '    return g\n')
P['r5v5r_b116_mix'] = 'def f(x):\n    m: int = 1\n    n: str\n    return m, n\n'
P['r5v5r_b116_default'] = 'def f(a: int, b: str = "x"):\n    c: float\n    return a, b, c\n'
P['r5v5r_b116_nested_bare'] = ('def f():\n    def g():\n        w: int\n        return w\n'
                               '    return g\n')

for name, src in P.items():
    with open(os.path.join(D, name + '.py'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(src)

rows = []
for stem in sorted(P):
    src = os.path.join(D, stem + '.py')
    pyc = os.path.join(D, stem + '.pyc')
    subprocess.run([sys.executable, '-c',
                    'import py_compile,sys;py_compile.compile(sys.argv[1],sys.argv[2],doraise=True,optimize=0)',
                    src, pyc])
    ok = os.path.join(D, stem + 'OK.py')
    subprocess.run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok])
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'), 'single', pyc],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = (r.stdout or '') + (r.stderr or '')
    status, us, ut, fails = None, None, None, []
    for line in out.splitlines():
        m = STAT_RE.search(line)
        if m:
            status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
        if FAIL_RE.match(line):
            fails.append(line.strip())
    rows.append({'pyc': 'test_repros/round5/%s.pyc' % stem, 'status': status,
                 'units_success': us, 'units_total': ut, 'failures': fails})
    print('%-10s %s/%s %s' % (status, us, ut, stem), flush=True)

with open(os.path.join(OUT, 'r5v5r_variant_results.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
tok = sum(r['units_success'] or 0 for r in rows)
tot = sum(r['units_total'] or 0 for r in rows)
print('-> variant units=%d/%d (%d files)' % (tok, tot, len(rows)))