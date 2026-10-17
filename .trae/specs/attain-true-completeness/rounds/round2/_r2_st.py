#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: line-trace _detect_boolop_short_circuit_chain for a start offset.
usage: _r2_st.py <pyc> <fn> <start_offset>
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

TARGET_FILE = os.path.join(ROOT, 'core', 'cfg', 'region_analyzer.py')
METHOD = '_detect_boolop_short_circuit_chain'
START = int(sys.argv[3])
events = []
active = []


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


def tracer(frame, event, arg):
    fn = frame.f_code.co_name
    if fn == METHOD:
        if event == 'call':
            sb = frame.f_locals.get('start_block')
            if sb is not None and sb.start_offset == START:
                active.append(True)
                events.append('CALL start=%d (b99_absorb=%s)' % (
                    START, frame.f_locals.get('_b99_absorb')))
            else:
                active.append(False)
        elif event == 'return':
            flag = active.pop() if active else False
            if flag:
                events.append('RETURN -> %s' % (None if arg is None else
                                                [(b.start_offset, o) for b, o in arg]))
        elif event == 'line' and active and active[-1]:
            events.append('%s:L%d' % (fn, frame.f_lineno))
            loc = frame.f_locals
            if frame.f_lineno == 33906:
                events.append('  pred_hit=@%s' % getattr(loc.get('_b99_pred_hit'), 'start_offset', None))
            elif frame.f_lineno == 33913:
                events.append('  prefixes=%s' % [(getattr(b, 'start_offset', b), o)
                                                 for b, o in (loc.get('_b99_prefixes') or [])])
            elif frame.f_lineno == 33919:
                events.append('  attach chain=%s prefixes=%s' % (
                    [(getattr(b, 'start_offset', b), o) for b, o in (loc.get('chain') or [])],
                    [(getattr(b, 'start_offset', b), o) for b, o in (loc.get('_b99_prefixes') or [])]))
            elif frame.f_lineno in (34047, 34108, 34131, 34132):
                events.append('  L%d chain=%s' % (frame.f_lineno,
                    [(getattr(b, 'start_offset', b), o) for b, o in (loc.get('chain') or [])]))
    elif active and active[-1] and frame.f_code.co_filename == TARGET_FILE:
        if event == 'line':
            events.append('%s:L%d' % (fn, frame.f_lineno))
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

out = []
prev = None
for e in events:
    if e.startswith('L') and e == prev:
        continue
    out.append(e)
    prev = e
print('\n'.join(out[:400]))
print('...total events=%d' % len(events))
