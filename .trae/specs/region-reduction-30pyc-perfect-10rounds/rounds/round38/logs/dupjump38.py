# -*- coding: utf-8 -*-
"""Round 38 hypothesis test on the largest pool cluster: 8 functions whose whole strict deficit
is ONE deleted jump instruction.

For each, print the real (unfiltered) instruction window around the deleted token plus the
product's source lines for the enclosing statement, so the shared shape can be read off
directly:  is the vanished jump a duplicate of the jump immediately before it (same opname,
same target)?  does the product instead emit one loop-level `continue`?

usage: python -X utf8 dupjump38.py --out=dupjump38.txt
"""
import difflib
import dis
import importlib.util
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r38gate/r38'
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

CASES = [
    ('IQCommon/api/klinedata.pyc', 'get_all_real_daily_kline'),
    ('IQCommon/strategy/wizard_quant_api.pyc', 'wizard_quant_check_limit'),
    ('IQCommon/util/common_func.pyc', 'fill_kline_data'),
    ('IQCommon/util/common_func.pyc', 'fill_kline_data_by_pre'),
    ('IQData/plugins/plugin_system_realquote/real_quote.pyc', 'one_prod_to_dataframe'),
    ('IQData/utils/common_func.pyc', 'fill_kline_data_by_pre'),
    ('fly/data/quote.pyc', 'is_delisting_stock_real'),
    ('fly/data/quote.pyc', 'one_prod_to_dataframe'),
]


def tok(i):
    if r10._is_jump(i.opname):
        return ('<JUMP>', r10._norm_jump_op(i.opname))
    return (str(r10._norm_arg(i)), i.opname)


lines = []
for rel, name in CASES:
    pyc = os.path.join(REPO, 'site-packages', rel.replace('/', os.sep))
    ok = os.path.join(ROOT, 'build_landed', rel[:-4].replace('/', '__') + 'OK.py')
    origs = r10._load_map(pyc)
    decs = r10._compile_map(ok)
    cands = [k for k in origs if k.split('.')[-1] == name]
    assert len(cands) == 1, (rel, name, cands)
    key = cands[0]
    o, d = r10.filtered(origs[key]), r10.filtered(decs[key])
    so, sd = [tok(i) for i in o], [tok(i) for i in d]
    dels = [(i1, i2) for tag, i1, i2, j1, j2 in
            difflib.SequenceMatcher(a=so, b=sd, autojunk=False).get_opcodes()
            if tag == 'delete' and i2 - i1 == len(so) - len(sd)]
    lines.append('=== %s :: %s   orig=%d decomp=%d   delete-hunks=%s' % (
        rel, name, len(so), len(sd), dels))
    assert len(dels) == 1, dels
    i1, i2 = dels[0]
    for k in range(max(0, i1 - 3), min(len(o), i2 + 3)):
        ins = o[k]
        mark = '  <<DELETED' if i1 <= k < i2 else ('(kept)' if k == i1 - 1 or k == i2 else '')
        lines.append('    #%-3d @%-5d %-30s %-22r %s%s%s' % (
            k, ins.offset, ins.opname,
            '<code>' if hasattr(ins.argval, 'co_code') else ins.argrepr,
            '' if ins.starts_line is None else 'L%d' % ins.starts_line,
            (' -> %s' % ins.argval) if r10._is_jump(ins.opname) else '', mark))
    # the duplicated-jump test: does an identical jump sit immediately before / after it?
    prev_same = i1 > 0 and so[i1 - 1] == so[i1]
    nxt_same = i2 < len(so) and so[i2] == so[i1]
    tgt_prev = (i1 > 0 and r10._is_jump(o[i1 - 1].opname) and o[i1 - 1].argval == o[i1].argval)
    lines.append('    deleted opname=%s target=%s | prev-instr identical token=%s '
                 'same-target-jump=%s | next-instr identical token=%s'
                 % (o[i1].opname, o[i1].argval, prev_same, tgt_prev, nxt_same))
    lines.append('    PRODUCT tail: ' + ' / '.join(
        '%s@%d' % (x.opname, x.offset) for x in d[max(0, i1 - 3):i1 + 2]))
text = '\r\n'.join(lines) + '\r\n'
io.open(os.path.join(ROOT, 'dupjump38.txt'), 'wb').write(text.encode('utf-8'))
print(text)
