# -*- coding: utf-8 -*-
"""scratch: compare a HYPOTHETICAL product source against the original pyc code object."""
import dis
import io
import marshal
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


pyc, srcpath, name = sys.argv[1], sys.argv[2], sys.argv[3]
oc = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
assert len(oc) == 1, len(oc)
src = io.open(srcpath, encoding='utf-8').read()
dc = [c for c in walk(compile(src, srcpath, 'exec'), []) if c.co_name == name]
assert len(dc) == 1, len(dc)
A, B = instrs(oc[0]), instrs(dc[0])
ka, kb = [norm(t) for t in A], [norm(t) for t in B]
print('orig=%d hyp=%d  EQUAL=%s' % (len(A), len(B), ka == kb))
sm = SequenceMatcher(None, ka, kb, autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal':
        continue
    print('HUNK %s orig[%d:%d]@%s hyp[%d:%d]@%s'
          % (tag, i1, i2, A[i1][2] if i2 > i1 else A[i1 - 1][2], j1, j2,
             B[j1][2] if j2 > j1 else B[j1 - 1][2]))
    for k in range(i1, i2):
        print('   O %5d %-28s %s' % (A[k][2], A[k][0], A[k][1][:60]))
    for k in range(j1, j2):
        print('   H %5d %-28s %s' % (B[k][2], B[k][0], B[k][1][:60]))
