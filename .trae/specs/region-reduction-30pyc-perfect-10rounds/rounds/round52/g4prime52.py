# -*- coding: utf-8 -*-
"""Per-code-object strict A/B for the officially-MOVED files (Round 52).

Compares the already-built products under build_landed (head) and build_cand.
"""
import importlib.util
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r52sc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

REL = ['IQCommon/api/klinedata.pyc',
       'IQEngine/plugins/plugin_fly_data/fly_api/order_api_trade.pyc',
       'IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc']


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
for rel in REL:
    pyc = os.path.join(REPO, 'site-packages', rel.replace('/', os.sep))
    fn = rel.replace('/', '__')[:-4] + 'OK.py'
    ph = 'D:/Temp/r52gate/build_landed/' + fn
    pc = 'D:/Temp/r52gate/build_cand/' + fn
    A, B = strict(ph, pyc), strict(pc, pyc)
    diff = [(k, A[k], B.get(k)) for k in sorted(set(A) | set(B)) if A.get(k) != B.get(k)]
    n_ok_a = sum(1 for v in A.values() if v == 'ok')
    n_ok_b = sum(1 for v in B.values() if v == 'ok')
    print('%-58s strict ok %d -> %d   changed=%d' % (rel[-58:], n_ok_a, n_ok_b, len(diff)))
    for k, a, b in diff:
        tag = 'FIXED' if b == 'ok' else ('BROKEN' if a == 'ok' else 'CHANGED')
        tot_fix += b == 'ok'
        tot_brk += a == 'ok' and b != 'ok'
        tot_chg += tag == 'CHANGED'
        print('   %-7s %-34s %s -> %s' % (tag, k.split('.')[-1][:34], a[:60], (b or '')[:60]))
print('TOTAL fixed=%d broken=%d changed=%d' % (tot_fix, tot_brk, tot_chg))
