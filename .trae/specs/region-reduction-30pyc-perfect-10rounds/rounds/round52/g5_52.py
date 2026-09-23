# -*- coding: utf-8 -*-
"""G5 for Round 52: landed core must reproduce the gated arm products byte-for-byte.

For every pyc whose product moved under the arm (G4 MOVED/IMPROVED list):
  1. decompile with the LANDED worktree core (no mirror),
  2. compare with D:/Temp/r52gate/build_c52ab/<arm product name>,
  3. write the repo <name>OK.py ONLY if the landed text equals the arm text.
Then the two canaries: fly/data/quotation.pyc (official + strict) and round16_sink.
"""
import hashlib
import importlib.util
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r52gate'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('r52sc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
_s2 = importlib.util.spec_from_file_location('pbv52', REPO + '/scripts/pyc_batch_verify.py')
pbv = importlib.util.module_from_spec(_s2)
_s2.loader.exec_module(pbv)
import pycdc
assert os.path.abspath(pycdc.__file__).replace('\\', '/').startswith(REPO.replace('\\', '/')), \
    'pycdc did not resolve to the worktree core'
print('pycdc = %s' % os.path.abspath(pycdc.__file__))

ARM = ['IQCommon/api/klinedata.pyc',
       'IQData/api/api_base.pyc',
       'fly/data/quote.pyc',
       'IQEngine/plugins/plugin_fly_data/fly_api/order_api_trade.pyc',
       'IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc']
ARM_ABS = ['test_repros/round3/r3_12_assert_absorbed_as_else.pyc']


def armname(p, under_sp=True):
    q = ((REPO.replace('\\', '/') + '/site-packages/' + p) if under_sp
         else (REPO.replace('\\', '/') + '/' + p)).replace('\\', '/')
    r0 = REPO.replace('\\', '/') + '/site-packages/'
    if q.startswith(r0):
        q = q[len(r0):]
    return q.replace('/', '__')[:-4].replace(':', '_') + 'OK.py'


n_written = n_ident = 0
for p in ARM + ARM_ABS:
    rel = p if p in ARM else p
    pyc = os.path.abspath((REPO + '/site-packages/' + p) if p in ARM else (REPO + '/' + p))
    txt = pycdc.decompile_pyc(pyc)
    prod = txt.encode('utf-8').decode('utf-8')
    arm_path = os.path.join(ROOT, 'build_c52ab', armname(p, p in ARM))
    arm_txt = io.open(arm_path, encoding='utf-8').read()
    same = prod == arm_txt
    n_ident += same
    if same and p in ARM:
        tgt = pyc[:-4] + 'OK.py'
        with io.open(tgt, 'w', encoding='utf-8') as f:
            f.write(prod)
        n_written += 1
    print('%-58s arm-identical=%-5s wrote=%s'
          % (os.path.basename(pyc), same, same and p in ARM))
    if not same:
        print('   !! landed %d B vs arm %d B' % (len(prod), len(arm_txt)))
print('landed-vs-arm identical: %d/%d ; products refreshed: %d' % (n_ident, len(ARM) + len(ARM_ABS), n_written))

print('---- canary quotation.pyc ----')
q = REPO + '/site-packages/fly/data/quotation.pyc'
txt = pycdc.decompile_pyc(os.path.abspath(q))
qp = ROOT + '/g5_quotation.py'
io.open(qp, 'w', encoding='utf-8', newline='').write(txt)
r = pbv.bytecode_diff(os.path.abspath(q), qp)
print('official %s/%s' % (r.get('matched_functions'), r.get('total_functions')))
o = r10._load_map(os.path.abspath(q))
d = r10._compile_map(qp)
bad = [n for n in sorted(set(o) & set(d)) if r10.strict_compare(o[n], d[n])[2]]
print('strict  %d/%d' % (len(set(o) & set(d)) - len(bad), len(set(o) & set(d))))
for b in bad:
    print('    ' + b)
