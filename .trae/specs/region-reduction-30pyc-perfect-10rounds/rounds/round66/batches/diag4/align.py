# -*- coding: utf-8 -*-
"""diag1 aligner: SequenceMatcher over orig-vs-decomp instruction sequences for ONE function.

usage: python -X utf8 align.py <pyc> <okpy> <funcname> [--max=N] [--pad=N]
Prints changed hunks with bytecode offsets + argrepr so we can pin which statements are missing.
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
    r = []
    for i in dis.get_instructions(code):
        if i.opname in ('CACHE',):
            continue
        r.append((i.opname, str(i.argrepr), i.offset))
    return r


def key(t):
    return t[0] + ' ' + t[1]


def srcmap(path):
    if not path or not os.path.isfile(path):
        return {}
    return {n + 1: l.rstrip('\n') for n, l in enumerate(io.open(path, encoding='utf-8', errors='replace').read().splitlines())}


def show(tag, seq, lo, hi, smap, limit=200):
    print('  --- %s [%d:%d] (%d instrs)' % (tag, lo, hi, hi - lo))
    for k in range(lo, min(hi, lo + limit)):
        op, arg, off = seq[k]
        line = ''
        if smap:
            ln = lineof(tag, seq, k)
            line = ' | ' + smap.get(ln, '')[:90] if ln else ''
        print('    %4d %5d %-26s %s%s' % (k, off, op, arg, line))


def lineof(tag, seq, k):
    return None


def cmp_func(orig_code, dec_code, o_src=None, d_src=None, maxhunk=40, pad=0):
    A = instrs(orig_code)
    B = instrs(dec_code)
    sm = SequenceMatcher(None, [key(t) for t in A], [key(t) for t in B], autojunk=False)
    ops = sm.get_opcodes()
    print('orig=%d decomp=%d  ratio=%.4f  opcodes=%s' % (len(A), len(B), sm.ratio(),
          [(o[0], o[1], o[2], o[3], o[4]) for o in ops if o[0] != 'equal'][:60]))
    for tag, i1, i2, j1, j2 in ops:
        if tag == 'equal':
            continue
        print('HUNK %-8s orig[%d:%d]@%s decomp[%d:%d]@%s' % (
            tag, i1, i2, A[i1][2] if i2 > i1 else '-', j1, j2, B[j1][2] if j2 > j1 else '-'))
        if i2 > i1:
            print('  ### ORIG only:')
            for k in range(i1, min(i2, i1 + maxhunk)):
                op, arg, off = A[k]
                print('    %5d %-26s %s' % (off, op, arg))
        if j2 > j1:
            print('  ### DECOMP only:')
            for k in range(j1, min(j2, j1 + maxhunk)):
                op, arg, off = B[k]
                print('    %5d %-26s %s' % (off, op, arg))


if __name__ == '__main__':
    pyc, okpy, name = sys.argv[1], sys.argv[2], sys.argv[3]
    want = int(os.environ.get('ALIGN_COUNT', '0'))
    oc = find_all(load_pyc(pyc), name)
    src = io.open(okpy, encoding='utf-8').read()
    dc = find_all(compile(src, okpy, 'exec'), name)
    print('orig candidates=%s decomp candidates=%s' % ([[c.co_firstlineno] for c in oc], [[c.co_firstlineno] for c in dc]))
    if len(oc) == 1 and len(dc) == 1:
        cmp_func(oc[0], dc[0])
    else:
        # pick closest counts
        best = None
        for a in oc:
            for b in dc:
                d = abs(len(instrs(a)) - len(instrs(b)))
                if best is None or d < best[0]:
                    best = (d, a, b)
        print('picked by closest count, delta=%d (lines %s vs %s)' % (best[0], best[1].co_firstlineno, best[2].co_firstlineno))
        cmp_func(best[1], best[2])
