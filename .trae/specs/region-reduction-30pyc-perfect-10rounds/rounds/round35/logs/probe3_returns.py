# -*- coding: utf-8 -*-
"""R35 read-only probe #3: which of the three emitted `return None` statements does the
original bytecode actually require?

The landed text of save_testds_to_json carries three `return None` lines
(indent 8 :345, indent 12 :353, indent 12 :367).  Probe #2 showed that dropping the last
one alone flips the file 14/15 -> 15/15.  Here every non-empty subset is dropped and
measured with the official ruler, so the predicate's boundary is measured rather than assumed.
"""
import importlib.util
import io
import itertools
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
OUT = r'D:/Temp/r35gate/r35'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')
_bv = importlib.util.spec_from_file_location('pbv', REPO + '/scripts/pyc_batch_verify.py')
pbv = importlib.util.module_from_spec(_bv)
_bv.loader.exec_module(pbv)

PYC = REPO + '/site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc'
PY = REPO + '/site-packages/IQEngine/plugins/plugin_system_risk_calculation/functionOK.py'
NAME = 'save_testds_to_json'

L = io.open(PY, encoding='utf-8-sig').read().replace('\r\n', '\n').split('\n')
RET = [k for k, l in enumerate(L) if l.strip() == 'return None' and 319 <= k <= 367]
assert [k + 1 for k in RET] == [345, 353, 367], [k + 1 for k in RET]

rep = ['return-None lines (1-based): %s' % [k + 1 for k in RET]]
for n in range(0, 4):
    for combo in itertools.combinations(RET, n):
        keep = [l for k, l in enumerate(L) if k not in combo]
        p = os.path.join(OUT, 'r3_%s.py' % ('_'.join(str(k + 1) for k in combo) or 'none'))
        io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(keep))
        res = pbv.bytecode_diff(PYC, p)
        row = [m for m in res['mismatches'] if str(m['name']).split('.')[-1] == NAME]
        rep.append('drop %-18s official %d/%d  target %s err=%r' % (
            [k + 1 for k in combo] or 'nothing', res['matched_functions'],
            res['total_functions'],
            'MATCH' if not row else '%d/%d jd%s td%s' % (row[0]['orig_count'], row[0]['decomp_count'],
                                                          row[0]['jump_diffs'], row[0]['true_diffs']),
            res.get('error')))
io.open(os.path.join(OUT, 'probe3_returns.txt'), 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(rep) + '\n')
print('\n'.join(rep))
