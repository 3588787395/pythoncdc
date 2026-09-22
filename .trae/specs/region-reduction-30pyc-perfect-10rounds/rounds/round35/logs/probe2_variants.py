# -*- coding: utf-8 -*-
"""R35 read-only probe #2: which direction is this defect -- over-emission or missing emission?

The landed product text of save_testds_to_json is re-measured verbatim and in four
edits, each through BOTH rulers (official bytecode_diff, strict _r10).  Nothing in the
repo is written; all variants go to scratch.
"""
import importlib.util
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
OUT = r'D:/Temp/r35gate/r35'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
_bv = importlib.util.spec_from_file_location('pbv', REPO + '/scripts/pyc_batch_verify.py')
pbv = importlib.util.module_from_spec(_bv)
_bv.loader.exec_module(pbv)

PYC = REPO + '/site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc'
PY = REPO + '/site-packages/IQEngine/plugins/plugin_system_risk_calculation/functionOK.py'
NAME = 'save_testds_to_json'

text = io.open(PY, encoding='utf-8-sig').read().replace('\r\n', '\n')
L = text.split('\n')
# locate the function body and its last line
DI = 319  # 0-based index of 'def save_testds_to_json('
assert L[DI].startswith('def save_testds_to_json('), L[DI]
last = DI
for j in range(DI + 1, len(L)):
    if L[j].strip():
        if (len(L[j]) - len(L[j].lstrip())) <= 0:
            break
        last = j
assert L[last].strip() == 'return None', repr(L[last])

variants = {
    'V0_landed': L[:],
    'V1_drop_last': L[:last] + L[last + 1:],
    'V2_last_becomes_pass': L[:last] + ['            pass'] + L[last + 1:],
    'V3_last_becomes_bare_return': L[:last] + ['            return'] + L[last + 1:],
    'V4_drop_last_add_funclevel': L[:last] + ['    return None'] + L[last + 1:],
}

orig_map = r10._load_map(PYC)
okey = [k for k in orig_map if k.split('.')[-1] == NAME][0]
o = orig_map[okey]

rep = []
for tag, v in variants.items():
    p = os.path.join(OUT, 'v_%s.py' % tag)
    io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(v))
    res = pbv.bytecode_diff(PYC, p)
    row = [m for m in res['mismatches'] if str(m['name']).split('.')[-1] == NAME]
    dmap = None
    cfile = os.path.join(OUT, 'v_%s.mpyc' % tag)
    import py_compile
    py_compile.compile(p, cfile=cfile, doraise=True, quiet=2)
    d = r10._load_map(cfile)[okey]
    kind, msg, defect = r10.strict_compare(o, d)
    rep.append('%-28s official %d/%d err=%r target_row=%s  strict defect=%s lo=%d ld=%d' % (
        tag, res['matched_functions'], res['total_functions'], res.get('error'),
        json.dumps({k: row[0][k] for k in ('orig_count', 'decomp_count', 'jump_diffs', 'true_diffs')},
                   ensure_ascii=False) if row else 'MATCHED',
        defect, len(r10.filtered(o)), len(r10.filtered(d))))
    if defect:
        import difflib

        def tok(x):
            if r10._is_jump(x.opname):
                return ('<JUMP>', r10._norm_jump_op(x.opname))
            return (r10._norm_arg(x), x.opname)
        fo, fd = r10.filtered(o), r10.filtered(d)
        for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [tok(x) for x in fo],
                                                         [tok(x) for x in fd], autojunk=False).get_opcodes():
            if t != 'equal':
                rep.append('      %-7s orig[%d:%d]%s %s -> decomp %s' % (
                    t, i1, i2, ('@%d' % fo[i1].offset) if i1 < len(fo) else '@EOF',
                    [x.opname for x in fo[i1:i2]], [x.opname for x in fd[j1:j2]]))
io.open(os.path.join(OUT, 'probe2_variants.txt'), 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(rep) + '\n')
print('\n'.join(rep))
