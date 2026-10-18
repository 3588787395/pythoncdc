#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 debug: line-trace the loop condition_block search for a function.
usage: _r2_looptrace.py <pyc> <fn>
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
from core.cfg.region_ast_generator import RegionASTGenerator

pyc = sys.argv[1]
name = sys.argv[2]
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])
targets = []


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)

TARGET_FILE = os.path.join(ROOT, 'core', 'cfg', 'region_analyzer.py')
events = []
active = []


def tracer(frame, event, arg):
    if frame.f_code.co_name == '_identify_loop_regions':
        if event == 'call':
            active.append(True)
            events.append('CALL')
        elif event == 'return':
            if active:
                active.pop()
                events.append('RETURN')
        elif event == 'line' and active:
            _loc = frame.f_lineno
            # log only lines in the condition search window + key vars
            if 5270 <= _loc <= 5770:
                cb = frame.f_locals.get('condition_block')
                events.append('L%d cb=@%s iwt=%s' % (
                    _loc,
                    cb.start_offset if cb is not None else None,
                    frame.f_locals.get('is_while_true')))
    return tracer


gen = RegionASTGenerator(cfg, top_level_code=None)
sys.settrace(tracer)
try:
    gen.region_analyzer.analyze()
finally:
    sys.settrace(None)
out = []
prev = None
for e in events:
    if e == prev:
        continue
    out.append(e)
    prev = e
print('\n'.join(out))
