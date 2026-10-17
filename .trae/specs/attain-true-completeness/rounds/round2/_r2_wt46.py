#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: line-trace _detect_boolop_conditional_chain for a given start_block offset.
usage: _r2_wt46.py <pyc> <fn> <start_offset>
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
METHOD = '_detect_boolop_conditional_chain'
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
    fname = frame.f_code.co_filename
    fn = frame.f_code.co_name
    if fn == METHOD:
        if event == 'call':
            try:
                sb = frame.f_locals.get('start_block')
                if sb is not None and sb.start_offset == START:
                    active.append(True)
                    events.append('CALL start=%d' % START)
            except Exception:
                pass
        elif event == 'return':
            if active:
                active.pop()
                events.append('RETURN -> %s' % (None if arg is None else
                                                [(b.start_offset, o) for b, o in arg]))
    elif active and fname == TARGET_FILE:
        if event == 'line':
            events.append('%s:L%d' % (fn, frame.f_lineno))
        elif event == 'call' and fn in ('_b1b_loop_body_run_continuation',
                                        '_boolop_shared_target_is_join',
                                        '_is_equivalent_exit_block'):
            try:
                blk = frame.f_locals.get('cand_block') or frame.f_locals.get('block')
                events.append('CALL %s @%s' % (fn, getattr(blk, 'start_offset', '?')))
            except Exception:
                events.append('CALL %s' % fn)
    return tracer


def local_tracer(frame, event, arg):
    if frame.f_code.co_name == METHOD:
        return tracer(frame, event, arg)
    return None


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
print('\n'.join(out))
print('---- regions after analyze ----')
for r in gen.region_analyzer.regions:
    print('  %s entry=@%s' % (type(r).__name__, r.entry.start_offset))
