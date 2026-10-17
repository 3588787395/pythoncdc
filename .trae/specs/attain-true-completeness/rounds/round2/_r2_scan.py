#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import sys

src = io.open(r'core/cfg/region_ast_generator.py', encoding='utf-8').read().splitlines()
lo = int(sys.argv[1])
hi = int(sys.argv[2])
for i, ln in enumerate(src[lo - 1:hi], start=lo):
    if "'Return'" in ln or 'SWAP' in ln or 'RETURN_VALUE' in ln:
        print(i, ln.rstrip()[:160])
