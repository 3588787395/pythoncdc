# -*- coding: utf-8 -*-
"""fix1: line up orig vs product instruction streams for the two failing jq
units and print every differing position (opname + argrepr + argval)."""
import dis
import io
import marshal
import sys
import types
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
PYC = REPO + r'\site-packages\IQCommon\strategy\jq_trans_module.pyc'
SRC = REPO + r'\site-packages\IQCommon\strategy\jq_trans_moduleOK.py'


def walk(c, out, pre=''):
    out.append((pre + c.co_name, c))
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            walk(k, out, pre + c.co_name + '.')
    return out


def key(i):
    if i.opname.startswith(('POP_JUMP', 'JUMP', 'FOR_ITER')) and i.arg is not None:
        a = 'J'
    else:
        a = i.argrepr
    return '%s %s' % (i.opname, a)


orig = marshal.loads(io.open(PYC, 'rb').read()[16:])
ocodes = dict(walk(orig, []))
prod = compile(io.open(SRC, encoding='utf-8').read(), SRC, 'exec')
pcodes = dict(walk(prod, []))

for qn in ('<module>.func_attribute_history_convert_code.replace_args',
           '<module>.func_get_bars_convert_code.replace_args'):
    a = ocodes[qn]
    b = pcodes.get(qn)
    if b is None:
        print('%s MISSING in product' % qn)
        continue
    A = list(dis.get_instructions(a))
    B = list(dis.get_instructions(b))
    ka = [key(i) for i in A]
    kb = [key(i) for i in B]
    print('\n=== %s  orig=%d prod=%d' % (qn, len(A), len(B)))
    sm = SequenceMatcher(None, ka, kb, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        print('  %s orig[%d:%d] prod[%d:%d]' % (tag, i1, i2, j1, j2))
        for i in range(i1, i2):
            print('     - orig %4d off=%-4d L%-4s %s' % (i, A[i].offset, A[i].starts_line, ka[i]))
        for j in range(j1, j2):
            print('     + prod %4d off=%-4d L%-4s %s' % (j, B[j].offset, B[j].starts_line, kb[j]))
