# -*- coding: utf-8 -*-
"""Official-filter aligner: SequenceMatcher over the SAME noise-filtered instruction
lists that testqouter/round1/base.compare_bytecode uses (NOP/PRECALL/EXTENDED_ARG/...
dropped), so delete/insert runs here correspond to what the official orig_count vs
decomp_count deficit actually is.

usage: python -X utf8 malign.py <pyc> <okpy> <funcname> [--ctx=N]
"""
import dis
import io
import marshal
import os
import sys
import types
from difflib import SequenceMatcher

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
from testqouter.round1.base import _filter_noise_instrs  # noqa: E402


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


def find_all(root, name):
    return [c for c in walk(root, []) if c.co_name == name]


def instrs(code):
    return [(i.opname, str(i.argrepr), i.offset) for i in _filter_noise_instrs(list(dis.get_instructions(code)))]


def key(t):
    return t[0] + ' ' + t[1]


def main(pyc, okpy, name, ctx=6, maxrun=400):
    oc = find_all(load_pyc(pyc), name)
    src = io.open(okpy, encoding='utf-8').read()
    dc = find_all(compile(src, okpy, 'exec'), name)
    if len(oc) == 1 and len(dc) == 1:
        o, d = oc[0], dc[0]
    else:
        best = None
        for a in oc:
            for b in dc:
                dd = abs(len(instrs(a)) - len(instrs(b)))
                if best is None or dd < best[0]:
                    best = (dd, a, b)
        o, d = best[1], best[2]
    A, B = instrs(o), instrs(d)
    print('FUNC %s  filtered orig=%d decomp=%d deficit=%d' % (name, len(A), len(B), len(A) - len(B)))
    sm = SequenceMatcher(None, [key(t) for t in A], [key(t) for t in B], autojunk=False)
    tot_del = tot_ins = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        print('HUNK %-8s orig[%d:%d] off %s..%s   decomp[%d:%d] off %s..%s  (o=%d d=%d)' % (
            tag, i1, i2, A[i1][2], A[i2 - 1][2], j1, j2,
            B[j1][2] if j2 > j1 else '-', B[j2 - 1][2] if j2 > j1 else '-', i2 - i1, j2 - j1))
        if i2 > i1:
            tot_del += i2 - i1
            print('  ### ORIG-only (MISSING from decomp):')
            for k in range(i1, min(i2, i1 + maxrun)):
                op, arg, off = A[k]
                print('    %5d %-30s %s' % (off, op, arg))
        if j2 > j1:
            tot_ins += j2 - j1
            print('  ### DECOMP-only (EXTRA / relocated):')
            for k in range(j1, min(j2, j1 + maxrun)):
                op, arg, off = B[k]
                print('    %5d %-30s %s' % (off, op, arg))
    print('SUMMARY missing_run_instrs=%d extra_run_instrs=%d' % (tot_del, tot_ins))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
