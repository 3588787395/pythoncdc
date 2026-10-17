#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: minimal trace of _detect_boolop_conditional_chain calls (no f_locals on others).
usage: _r2_mt.py <pyc> <fn>
"""
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

METHOD = '_detect_boolop_conditional_chain'
events = []


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


def tracer(frame, event, arg):
    if frame.f_code.co_name == METHOD:
        if event == 'call':
            sb = frame.f_locals.get('start_block')
            events.append(('CALL', sb.start_offset if sb is not None else None))
        elif event == 'return':
            events.append(('RET', None if arg is None else
                           [(b.start_offset, o) for b, o in arg]))
    return tracer


pyc = sys.argv[1]
name = sys.argv[2]
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])
targets = []
find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
sys.settrace(tracer)
try:
    gen.region_analyzer.analyze()
finally:
    sys.settrace(None)
for ev in events:
    print(ev)
print('---- regions ----')
for r in gen.region_analyzer.regions:
    print('  %s entry=@%s' % (type(r).__name__, r.entry.start_offset))
