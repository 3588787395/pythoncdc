# -*- coding: utf-8 -*-
"""Round 30 first-hand strict-ruler hunk reading for one function of one (pyc, OK.py) pair.

usage: hunks30.py <pyc> <ok.py> <function-name-tail>
Prints the filtered lengths, the number of non-equal alignment blocks, and each block's
kind + real byte offsets on both sides.
"""
import difflib
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
name = [k for k in origs if k.endswith(tail)]
assert len(name) == 1, name
name = name[0]
def tok(i):
    if r10._is_jump(i.opname):
        return ('<JUMP>', r10._norm_jump_op(i.opname))
    return (r10._norm_arg(i), i.opname)


o = r10.filtered(origs[name])
d = r10.filtered(decs[name])
to = [tok(i) for i in o]
td = [tok(i) for i in d]
sm = difflib.SequenceMatcher(None, to, td, autojunk=False)
blocks = [x for x in sm.get_opcodes() if x[0] != 'equal']
print('%s  %s' % (name, tail))
print('  filtered orig=%d decomp=%d delta=%+d   non-equal blocks=%d'
      % (len(o), len(d), len(d) - len(o), len(blocks)))


def off(seq, i):
    return seq[i].offset if i < len(seq) else (seq[-1].offset if seq else -1)


for k, (tag, a0, a1, b0, b1) in enumerate(blocks, 1):
    print('  H%d %-8s orig[%d:%d] @%d..%d  ->  decomp[%d:%d] @%d..%d   n=%d/%d'
          % (k, tag, a0, a1, off(o, a0), off(o, max(a1 - 1, 0)),
             b0, b1, off(d, b0), off(d, max(b1 - 1, 0)), a1 - a0, b1 - b0))
    for i in range(a0, min(a1, a0 + 6)):
        print('        o  @%-5d %s' % (o[i].offset, tok(o[i])))
    for i in range(b0, min(b1, b0 + 6)):
        print('        d  @%-5d %s' % (d[i].offset, tok(d[i])))
