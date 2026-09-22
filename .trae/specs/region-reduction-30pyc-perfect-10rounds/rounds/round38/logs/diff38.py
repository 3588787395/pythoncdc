# -*- coding: utf-8 -*-
"""Round 38 read-only diagnostic: aligned instruction-sequence diff for one function.

Uses the same token normalisation as the strict gate (_r10_strict_check.strict_compare) but
aligns the two sequences with difflib instead of failing on the first difference, so a whole
hunk (missing block / inserted block / transposition) is visible at once.

usage: python -X utf8 diff38.py --pyc=<abs.pyc> --ok=<absOK.py> --tail=<function-name-tail>
                                [--ctx=3]
"""
import difflib
import dis
import importlib.util
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
kw = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)


def tok(i):
    if r10._is_jump(i.opname):
        return ('<JUMP>', r10._norm_jump_op(i.opname))
    return (str(r10._norm_arg(i)), i.opname)


def line(i):
    if r10._is_jump(i.opname):
        return '%-4d %-30s -> %-14s %s' % (i.offset, i.opname, i.argval,
                                           '' if i.starts_line is None else 'L%d' % i.starts_line)
    av = '<code>' if hasattr(i.argval, 'co_code') else i.argrepr
    return '%-4d %-30s %-24r %s' % (i.offset, i.opname, av,
                                    '' if i.starts_line is None else 'L%d' % i.starts_line)


name = kw['name'] if 'name' in kw else kw['tail']
origs = r10._load_map(kw['pyc'])
decs = r10._compile_map(kw['ok'])
cands = [k for k in origs if k.endswith(kw['tail'])]
assert len(cands) == 1, cands
key = cands[0]
o, d = r10.filtered(origs[key]), r10.filtered(decs[key])
so, sd = [tok(i) for i in o], [tok(i) for i in d]
print('=== %s  %s  orig=%d decomp=%d delta=%+d ===' % (key, os.path.basename(kw['pyc']),
                                                       len(so), len(sd), len(sd) - len(so)))
sm = difflib.SequenceMatcher(a=so, b=sd, autojunk=False)
CTX = int(kw.get('ctx', 3))
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal':
        continue
    print('\n--- %s  orig[%d:%d] decomp[%d:%d] ---' % (tag, i1, i2, j1, j2))
    for k in range(max(0, i1 - CTX), i1):
        print('    ctx  O %s' % line(o[k]))
    for k in range(i1, i2):
        print('    -O   %s' % line(o[k]))
    for k in range(j1, j2):
        print('    +D   %s' % line(d[k]))
    for k in range(i2, min(len(o), i2 + CTX)):
        print('    ctx  O %s' % line(o[k]))
if sm.ratio() > 0.999 and so == sd:
    print('(sequences identical token-wise)')
