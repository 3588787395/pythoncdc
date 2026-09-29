# -*- coding: utf-8 -*-
"""probe: find a minimal synthetic source that reproduces the fix2 defect under head.

For each candidate: compile -> decompile with landed and ec_afgd5b -> mandated verify.
Print verdicts so we can pick the repro.
"""
import io
import os
import py_compile
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = r'F:\Downloads\pythoncdc-main'
VERIFY = os.path.join(REPO, 'scripts', 'pyc_verify.py')
sys.stdout.reconfigure(encoding='utf-8')

OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)

CANDS = {
    'a_try_for_break_tail': '''# -*- coding: utf-8 -*-
def a_try_for_break_tail(items, log):
    hit = 0
    try:
        with open("nul") as fh:
            for it in items:
                if it < 0:
                    break
                hit += it
    except BaseException:
        return -1
    del items
    log.append(hit)
    return hit
''',
    'b_try_for_break_last': '''# -*- coding: utf-8 -*-
def b_try_for_break_last(items):
    hit = 0
    try:
        for it in items:
            if not it:
                break
            hit += 1
    except BaseException:
        return -1
    return hit
''',
    'c_if_tail_pure': '''# -*- coding: utf-8 -*-
def c_if_tail_pure(items, flag):
    if flag:
        for it in items:
            if it:
                break
    return None
''',
    'd_if_else_tail_stmt': '''# -*- coding: utf-8 -*-
def d_if_else_tail_stmt(items, flag, log):
    if flag:
        return 1
    else:
        for it in items:
            if it:
                break
        del items
        log.append("x")
    return 0
''',
    'e_while_tail': '''# -*- coding: utf-8 -*-
def e_while_tail(items, log):
    hit = 0
    while items:
        it = items.pop()
        if it < 0:
            break
        hit += it
    del items
    log.append(hit)
    return hit
''',
}


def sha(t):
    import hashlib
    return hashlib.sha256(t.encode('utf-8')).hexdigest()[:16]


for name, src in CANDS.items():
    p = os.path.join(HERE, name + '.py')
    pyc = os.path.join(HERE, name + '.pyc')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(src)
    py_compile.compile(p, cfile=pyc, doraise=True)
    got = {}
    for arm in ('landed', 'ec_afgd5b'):
        out = os.path.join(OUT, '%s_%s.py' % (arm, name))
        subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8',
                        os.path.join(HERE, '..', 'run_arm.py'), arm, pyc, out],
                       capture_output=True, text=True, timeout=200, errors='replace')
        text = io.open(out, encoding='utf-8').read()
        r = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8', VERIFY, 'single',
                            pyc, '--source', out], capture_output=True, text=True,
                           timeout=200, errors='replace')
        tail = [l for l in (r.stdout or '').split('\n') if l.startswith('[single] status')]
        got[arm] = (sha(text), tail[-1].strip() if tail else (r.stdout or '')[-160:])
    diff = got['landed'][0] != got['ec_afgd5b'][0]
    print('%-24s diff=%-5s landed=%s | cand=%s'
          % (name, diff, got['landed'][1], got['ec_afgd5b'][1]))
