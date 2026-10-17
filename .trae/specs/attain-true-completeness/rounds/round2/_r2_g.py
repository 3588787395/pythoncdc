#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: range grep. usage: _r2_g.py <file> <lo> <hi> <pattern>"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
path = sys.argv[1]
lo, hi = int(sys.argv[2]), int(sys.argv[3])
pat = re.compile(sys.argv[4])
for i, l in enumerate(open(path, encoding='utf-8', errors='replace'), 1):
    if lo <= i <= hi and pat.search(l):
        print('%6d| %s' % (i, l.rstrip()[:170]))
