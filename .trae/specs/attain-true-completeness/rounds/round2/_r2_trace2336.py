#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: line-trace the generation of one BoolOpRegion (by entry offset) to find
where the statement emission dies for the trade_info_utils full-chain case."""
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

pyc = sys.argv[1]
name = sys.argv[2]
entry_off = int(sys.argv[3])
lo = int(sys.argv[4]) if len(sys.argv) > 4 else 1
hi = int(sys.argv[5]) if len(sys.argv) > 5 else 99999

data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


targets = []
find_code(code, name, targets)
co = targets[-1]

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)

lines_seq = []
_collect = False


def tracer(frame, event, arg):
    if event == 'line':
        fn = frame.f_code.co_filename
        if os.path.basename(fn) == 'region_ast_generator.py':
            ln = frame.f_lineno
            if _collect and lo <= ln <= hi:
                lines_seq.append(ln)
    return tracer


_gb = gen._generate_boolop


def gb(region, *a, **k):
    global _collect
    if region.entry.start_offset == entry_off:
        _collect = True
        sys.settrace(tracer)
        try:
            r = _gb(region, *a, **k)
        finally:
            sys.settrace(None)
            _collect = False
        sys.stdout.write('result items: %s\n' % (len(r) if isinstance(r, list)
                                                 else type(r).__name__))
    return _gb(region, *a, **k)


gen._generate_boolop = gb
gen.generate()

collapsed = []
prev = None
for ln in lines_seq:
    if ln != prev:
        collapsed.append(ln)
        prev = ln
sys.stdout.write('\n'.join(str(x) for x in collapsed))
sys.stdout.write('\n---- total lines: %d\n' % len(lines_seq))
