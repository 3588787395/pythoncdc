# -*- coding: utf-8 -*-
"""dump.py — read-only line dumper for the mirror's generator/analyzer.

usage: python -X utf8 dump.py <relfile> <lo> <hi>
Writes UTF-8 to stdout with replacement so GBK consoles don't crash.
"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace',
                              line_buffering=True)

rel, lo, hi = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
src = open(rel, encoding='utf-8-sig', errors='replace').read().replace('\r\n', '\n').split('\n')
for i in range(lo, min(hi, len(src)) + 1):
    print('%6d %s' % (i, src[i - 1][:200]))
