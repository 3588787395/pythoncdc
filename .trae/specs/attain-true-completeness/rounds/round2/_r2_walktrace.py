#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: trace _detect_boolop_conditional_chain line events + current block."""
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


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


targets = []
find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)

log = []
last = [None]


def tracer(frame, event, arg):
    if event == 'call':
        if frame.f_code.co_name == '_detect_boolop_conditional_chain':
            return tracer
        return None
    if event == 'line':
        cur = frame.f_locals.get('current')
        cur_off = getattr(cur, 'start_offset', None)
        chain = frame.f_locals.get('chain')
        cl = None
        if isinstance(chain, list):
            cl = [(getattr(b, 'start_offset', None), o) for b, o in chain]
        key = (cur_off, tuple(cl) if cl else cl)
        if key != last[0]:
            log.append('L%-6d current=@%s chain=%s' % (frame.f_lineno, cur_off, cl))
            last[0] = key
    return tracer


sys.settrace(tracer)
try:
    gen.generate()
finally:
    sys.settrace(None)

for line in log:
    print(line)
