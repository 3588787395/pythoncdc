# -*- coding: utf-8 -*-
"""diag1: normalized substantive-hunk table for ONE function.

Same alignment as align.py but with the two unavoidable noise sources neutralised:
  * every jump/branch argument (a bytecode offset) -> 'J'   (relocation noise)
  * every nested-code-object argument repr         -> 'CODEOBJ' (carries file/line of the product)
Only remaining hunks are real structural defects.  usage:
  python -X utf8 logs/nhunks.py <pyc> <okpy> <func> [--ctx=N]
"""
import dis
import io
import json
import marshal
import os
import sys
import types
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding='utf-8')

JUMPS = ('JUMP', 'BRANCH', 'RETURN_GENERATOR')


def load_pyc(path):
    data = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    raise SystemExit('cannot unmarshal %s' % path)


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def instrs(code):
    return [(i.opname, str(i.argrepr), i.offset) for i in dis.get_instructions(code)
            if i.opname != 'CACHE']


def norm(t):
    op, arg, off = t
    if op.startswith(JUMPS) or arg.startswith('to ') or 'group' in arg:
        return op + ' J'
    if '<code object' in arg:
        return op + ' CODEOBJ'
    return op + ' ' + arg


def main(pyc, okpy, name, ctx=6):
    oc = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
    assert len(oc) == 1, [c.co_firstlineno for c in oc]
    dc = [c for c in walk(compile(io.open(okpy, encoding='utf-8').read(), okpy, 'exec'), [])
          if c.co_name == name]
    assert len(dc) == 1, [c.co_firstlineno for c in dc]
    A, B = instrs(oc[0]), instrs(dc[0])
    ka, kb = [norm(t) for t in A], [norm(t) for t in B]
    sm = SequenceMatcher(None, ka, kb, autojunk=False)
    ops = [o for o in sm.get_opcodes() if o[0] != 'equal']
    print('# %s :: %s   orig=%d decomp=%d  substantive-hunks=%d'
          % (os.path.basename(pyc), name, len(A), len(B), len(ops)))
    for tag, i1, i2, j1, j2 in ops:
        oa = A[i1][2] if i2 > i1 else (A[max(0, i1 - 1)][2] if i1 else -1)
        ob = B[j1][2] if j2 > j1 else (B[max(0, j1 - 1)][2] if j1 else -1)
        print('HUNK %-8s orig[%d:%d]@%d(%d) decomp[%d:%d]@%d(%d)'
              % (tag, i1, i2, oa, i2 - i1, j1, j2, ob, j2 - j1))
        for lbl, seq, lo, hi in (('ORIG', A, i1, i2), ('DECOMP', B, j1, j2)):
            if hi <= lo:
                continue
            for k in range(max(0, lo - ctx), min(len(seq), hi + ctx)):
                mark = '   ' if (lo <= k < hi) else ' . '
                print('  %s%5d %-28s %s' % (mark, seq[k][2], seq[k][0], seq[k][1][:60]))


if __name__ == '__main__':
    kw = dict(x[2:].split('=', 1) for x in sys.argv[4:])
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(kw.get('ctx', 6)))
