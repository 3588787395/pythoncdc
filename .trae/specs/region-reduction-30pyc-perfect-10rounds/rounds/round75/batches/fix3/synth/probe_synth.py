# -*- coding: utf-8 -*-
"""fix3 synth probe: try candidate repro shapes + nested-try negative on both arms."""
import hashlib
import io
import json
import os
import py_compile
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
REPO = r'F:\Downloads\pythoncdc-main'
VERIFY = os.path.join(REPO, 'scripts', 'pyc_verify.py')
RUN = r'D:\Temp\opencode\r75gate\fix2\run_arm.py'

SHAPES = {
    's1_or_nested': '''def s1(a, b, c, d):
    if a is None:
        if not b or c:
            return 1
        elif d:
            return 2
        return 3
    elif a == 0:
        return 4
    return 5
''',
    's2_or_ret_else': '''def s2(a, b, c):
    if a is None:
        if not b or c:
            return 1
        else:
            return 2
    return 3
''',
    's3_chain_like_wizard': '''def s3(a, b, c, d):
    if a is None:
        if not b or c:
            return 1
        if a == 0:
            return 2
        if d is None:
            if not b or c:
                return 3
            return 4
        return 5
    elif a == 1:
        return 6
    return 7
''',
    's4_or_toplevel': '''def s4(a, b, c):
    if not a or b:
        return 1
    return 2
''',
    's5_or_mid_chain': '''def s5(a, b, c, d):
    if a is None:
        if not b or c:
            return 1
        elif d == 0:
            return 2
        return 3
    elif a == 1:
        if not b or c:
            return 4
        return 5
    return 6
''',
}

NEG = '''def neg_nested_try(x):
    try:
        try:
            return 10 / x
        except ZeroDivisionError:
            return -1
    except Exception:
        return -2


def neg_nested_try_loop(n):
    total = 0
    try:
        try:
            for i in range(n):
                total += i
        except ValueError:
            total = 0
        return total
    except RuntimeError:
        return -3
'''


def sha(t):
    return hashlib.sha256(t.encode('utf-8')).hexdigest()[:16]


def decompile(arm, pyc, out):
    r = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8', RUN, arm, pyc, out],
                       capture_output=True, text=True, timeout=280, errors='replace')
    return os.path.isfile(out)


def verify(pyc, out):
    r = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8', VERIFY, 'single', pyc,
                        '--source', out], capture_output=True, text=True, timeout=280,
                       errors='replace')
    tail = [l for l in (r.stdout or '').split('\n') if l.startswith('[single] status')]
    return tail[-1].strip() if tail else (r.stdout or '')[-160:]


rows = {}
for name, src in list(SHAPES.items()) + [('neg75_nested', NEG)]:
    p = os.path.join(HERE, name + '.py')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(
        '# -*- coding: utf-8 -*-\n# [R75 fix3 synth]\n' + src)
    py_compile.compile(p, cfile=os.path.join(HERE, name + '.pyc'), doraise=True)
    pyc = os.path.join(HERE, name + '.pyc')
    row = {}
    for arm in ('landed', 'abdef'):
        out = os.path.join(HERE, 'out', '%s_%s.py' % (arm, name))
        if os.path.exists(out):
            os.remove(out)
        if not decompile(arm, pyc, out):
            row[arm] = ('DECOMPILE-FAIL', '')
            continue
        text = io.open(out, encoding='utf-8').read()
        row[arm] = (sha(text), verify(pyc, out))
    rows[name] = row
    print(name)
    for arm in ('landed', 'abdef'):
        print('    %-8s %s  %s' % (arm, row[arm][0], row[arm][1]))
    if name.startswith('neg'):
        print('    neg_sha_identical=%s' % (row['landed'][0] == row['abdef'][0]))
    else:
        print('    differ=%s head_failure=%s cand_success=%s' % (
            row['landed'][0] != row['abdef'][0],
            'failure' in row['landed'][1],
            'status=success' in row['abdef'][1]))

io.open(os.path.join(HERE, 'out', 'probe.json'), 'w', encoding='utf-8', newline='\n').write(
    json.dumps({k: {a: list(v) for a, v in r.items()} for k, r in rows.items()},
               ensure_ascii=False, indent=1))
