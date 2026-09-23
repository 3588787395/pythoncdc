# -*- coding: utf-8 -*-
"""G4' for Round 52: per-code-object strict A/B for every officially-MOVED/IMPROVED file.

usage: python -X utf8 g4prime52b.py <head-build> <cand-build>
Compares products already written by the G4 runs (no core involvement).
"""
import importlib.util
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')
A_DIR = os.path.abspath(sys.argv[1])
B_DIR = os.path.abspath(sys.argv[2])
_s = importlib.util.spec_from_file_location('r52sc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

REL = ['IQCommon/api/klinedata.pyc',
       'IQData/api/api_base.pyc',
       'fly/data/quote.pyc',
       'IQEngine/plugins/plugin_fly_data/fly_api/order_api_trade.pyc',
       'IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc']
ABS = ['test_repros/round3/r3_12_assert_absorbed_as_else.pyc']


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


tot_fix = tot_brk = tot_chg = 0
ALL = [(REPO + '/site-packages/' + r) for r in REL] + [(REPO + '/' + r) for r in ABS]
for p in ALL:
    pyc = os.path.abspath(p.replace('/', os.sep))
    rel = os.path.basename(pyc)
    fn = prodname(p)
    ph = os.path.join(A_DIR, fn)
    pc = os.path.join(B_DIR, fn)
    if not (os.path.exists(ph) and os.path.exists(pc)):
        print('%-58s SKIP (product missing: %s)' % (rel, fn))
        continue
    A, B = strict(ph, pyc), strict(pc, pyc)
    diff = [(k, A[k], B.get(k)) for k in sorted(set(A) & set(B)) if A[k] != B[k]]
    n_ok_a = sum(1 for v in A.values() if v == 'ok')
    n_ok_b = sum(1 for v in B.values() if v == 'ok')
    print('%-58s strict ok %d/%d -> %d/%d   changed=%d'
          % (p[-58:], n_ok_a, len(A), n_ok_b, len(B), len(diff)))
    for k, a, b in diff:
        tag = 'FIXED' if b == 'ok' else ('BROKEN' if a == 'ok' else 'CHANGED')
        tot_fix += b == 'ok'
        tot_brk += a == 'ok' and b != 'ok'
        tot_chg += tag == 'CHANGED'
        print('   %-7s %-36s %s -> %s' % (tag, k.split('.')[-1][:36], a[:62], (b or '')[:62]))
print('TOTAL fixed=%d broken=%d changed=%d' % (tot_fix, tot_brk, tot_chg))
