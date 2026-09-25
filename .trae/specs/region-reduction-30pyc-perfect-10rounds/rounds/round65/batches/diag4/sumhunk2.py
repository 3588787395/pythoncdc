# -*- coding: utf-8 -*-
"""diag4: hunk summary filtered to |net| >= threshold OR big blocks.

usage: python -X utf8 sumhunk2.py logs/AL_x.txt [maxops] [minnet]
"""
import io
import re
import sys

op_re = re.compile(r'^\s+(\d+) (\S+)\s*(.*)$')
hunk_re = re.compile(r'^HUNK (\w+)\s+orig\[(\d+):(\d+)\]@(\S+) decomp\[(\d+):(\d+)\]@(\S+)')


def fmt(xs, n):
    out = ['%d:%s %s' % (off, op, arg[:24]) for off, op, arg in xs[:n]]
    if len(xs) > n:
        out.append('...+%d' % (len(xs) - n))
    return ' | '.join(out)


def main():
    path = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    minnet = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    L = io.open(path, encoding='utf-8').read().splitlines()
    print('## %s' % path)
    print(L[1][:120] if len(L) > 1 else '')
    i = 2
    while i < len(L):
        m = hunk_re.match(L[i])
        if not m:
            i += 1
            continue
        tag, i1, i2, o1, j1, j2, o2 = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4), int(m.group(5)), int(m.group(6)), m.group(7)
        i += 1
        orig, dec = [], []
        side = None
        while i < len(L) and not hunk_re.match(L[i]):
            s = L[i]
            if s.strip() == '### ORIG only:':
                side = orig
            elif s.strip() == '### DECOMP only:':
                side = dec
            else:
                mm = op_re.match(s)
                if mm and side is not None:
                    side.append((int(mm.group(1)), mm.group(2), mm.group(3).strip()))
            i += 1
        if max(i2 - i1, j2 - j1) < minnet:
            continue
        print('HUNK %-7s orig[%d:%d]@%s(%d) decomp[%d:%d]@%s(%d) net=%+d' % (
            tag, i1, i2, o1, i2 - i1, j1, j2, o2, j2 - j1, (j2 - j1) - (i2 - i1)))
        if orig:
            print('   O: %s' % fmt(orig, n))
        if dec:
            print('   D: %s' % fmt(dec, n))


main()
