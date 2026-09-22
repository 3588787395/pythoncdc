# -*- coding: utf-8 -*-
"""Round 32 read-only helper: print both sides' instruction sequences (opname, normalised arg,
jump target offsets) for one function of one (pyc, OK.py) pair.

usage: python -X utf8 dump32.py <pyc> <ok.py> <function-name-tail>
"""
import dis
import importlib.util
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

pyc, ok, tail = sys.argv[1], sys.argv[2], sys.argv[3]
origs = r10._load_map(pyc)
decs = r10._compile_map(ok)
names = [k for k in origs if k.endswith(tail)]
assert len(names) == 1, names
name = names[0]


def show(tag, code):
    print('--- %s %s  co_code len=%d ---' % (tag, name, len(code.co_code)))
    for i in dis.get_instructions(code):
        j = ''
        if i.starts_line is not None:
            j += ' line=%d' % i.starts_line
        if r10._is_jump(i.opname):
            j += ' -> %s' % i.argval
        print('  @%-4d %-24s %-28r%s' % (i.offset, i.opname,
                                         '<code>' if hasattr(i.argval, 'co_code') else i.argrepr, j))


show('ORIGINAL', origs[name])
show('DECOMPILED', decs[name])
print('filtered orig=%d decomp=%d' % (len(r10.filtered(origs[name])), len(r10.filtered(decs[name]))))
