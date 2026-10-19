#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 head-sim: disable B112 gate at runtime, decompile a pyc (simulate HEAD core)."""
import io
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import region_ast_generator as RAG

RAG.RegionASTGenerator._b112_async_gen_yield_await_gate = lambda self, block: None

import pycdc

pyc = sys.argv[1]
out = sys.argv[2]
src = pycdc.decompile_pyc(pyc)
open(out, 'w', encoding='utf-8').write(src)
print('written', out)
