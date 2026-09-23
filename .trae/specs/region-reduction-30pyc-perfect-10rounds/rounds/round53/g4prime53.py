# -*- coding: utf-8 -*-
"""G4' for Round 53: per-code-object strict A/B for every file the G4 official ruler says
changed (MOVED/IMPROVED/REGRESSION).  Compares products already written by the two G4 runs,
so no core is loaded.

usage: python -X utf8 g4prime53.py <head-build> <cand-build> <pyc-paths-file>
"""
import importlib.util
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')
A_DIR = os.path.abspath(sys.argv[1])
B_DIR = os.path.abspath(sys.argv[2])
LIST = sys.argv[3]
_s = importlib.util.spec_from_file_location('r53sc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)


def prodname(p):
    """Same mapping the G4 runner uses: site-packages-relative rel -> '__'-joined
    stem + 'OK.py'; paths outside site-packages keep their whole absolute form."""
    p = p.replace('\\', '/')
    r0 = REPO.replace('\\', '/') + '/site-packages/'
    if p.startswith(r0):
        p = p[len(r0):]
    return p.replace('/', '__')[:-4].replace(':', '_') + 'OK.py'


def strict(prod, pyc):
    o = r10._load_map(pyc)
    d = r10._compile_map(prod)
    out = {}
    for name in sorted(set(o) & set(d)):
        kind, msg, isdef = r10.strict_compare(o[name], d[name])
        out[name] = ('%s %s' % (kind, msg)) if isdef else 'ok'
    for name in sorted(set(o) - set(d)):
        out[name] = 'MISSING-IN-PRODUCT'
    return out


rows = []
tot_fix = tot_brk = tot_chg = 0
for p in [l.strip() for l in io.open(LIST, encoding='utf-8') if l.strip()]:
    pyc = os.path.abspath(p.replace('\\', '/').replace('/', os.sep))
    fn = prodname(p)
    ph = os.path.join(A_DIR, fn)
    pc = os.path.join(B_DIR, fn)
    if not (os.path.exists(ph) and os.path.exists(pc)):
        print('%-58s SKIP (product missing: %s)' % (pyc[-58:], fn))
        continue
    A, B = strict(ph, pyc), strict(pc, pyc)
    diff = [(k, A[k], B.get(k)) for k in sorted(set(A) & set(B)) if A[k] != B[k]]
    n_ok_a = sum(1 for v in A.values() if v == 'ok')
    n_ok_b = sum(1 for v in B.values() if v == 'ok')
    print('%-58s strict ok %d/%d -> %d/%d   changed=%d'
          % (pyc[-58:], n_ok_a, len(A), n_ok_b, len(B), len(diff)))
    for k, a, b in diff:
        tag = 'FIXED' if b == 'ok' else ('BROKEN' if a == 'ok' else 'CHANGED')
        tot_fix += b == 'ok'
        tot_brk += a == 'ok' and b != 'ok'
        tot_chg += tag == 'CHANGED'
        print('   %-7s %-36s %s -> %s' % (tag, k.split('.')[-1][:36], a[:62], (b or '')[:62]))
    rows.append({'path': pyc, 'ok_head': n_ok_a, 'ok_cand': n_ok_b, 'total': len(A),
                 'diff': [[k, a, b] for k, a, b in diff]})
print('TOTAL fixed=%d broken=%d changed=%d' % (tot_fix, tot_brk, tot_chg))
io.open(os.path.join(os.path.dirname(os.path.abspath(LIST)),
                     'g4prime53_' + os.path.basename(LIST).replace('.txt', '') + '.json'),
        'w', encoding='utf-8').write(json.dumps(
            {'fixed': tot_fix, 'broken': tot_brk, 'changed': tot_chg, 'rows': rows},
            ensure_ascii=False, indent=1))
