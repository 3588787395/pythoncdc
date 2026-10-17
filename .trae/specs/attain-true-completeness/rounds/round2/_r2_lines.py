#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""grep helper: print lines in file range matching simple substring set."""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
path, lo, hi = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
pats = sys.argv[4:]
lines = open(path, encoding='utf-8').read().splitlines()
for i in range(lo - 1, min(hi, len(lines))):
    l = lines[i]
    if any(p in l for p in pats):
        print(i + 1, l)
