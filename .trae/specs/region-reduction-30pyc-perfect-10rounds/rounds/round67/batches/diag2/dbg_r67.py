# -*- coding: utf-8 -*-
"""R67-diag2 read-only trace: which lines of _identify_conditional_regions run for a
given candidate condition block (by start_offset).  sys.settrace only, no repo writes.

usage: python -X utf8 dbg_r67.py <pyc> <func> <cond_block_offset>
"""
import io
import marshal
import os
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

pyc, name, want = sys.argv[1], sys.argv[2], int(sys.argv[3])
data = io.open(pyc, 'rb').read()
root = marshal.loads(data[16:])


def walk(c, o):
    o.append(c)
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            walk(k, o)
    return o


code = [c for c in walk(root, []) if c.co_name == name][0]
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

cfg = build_cfg(code)
gen = RegionASTGenerator(cfg, top_level_code=None)
ra = gen.region_analyzer

EVENTS = []
TARGET = {'co_name': '_identify_conditional_regions'}


def tracer(frame, event, arg):
    co = frame.f_code
    if co.co_name != TARGET['co_name']:
        return None
    if 'region_analyzer' not in os.path.basename(co.co_filename):
        return None
    if event == 'call':
        return tracer
    if event == 'line':
        b = frame.f_locals.get('block')
        off = getattr(b, 'start_offset', None) if b is not None else None
        EVENTS.append((co.co_filename, frame.f_lineno, off))
        return tracer
    return tracer


sys.settrace(tracer)
regions = ra.analyze()
sys.settrace(None)

seq = [ln for _f, ln, off in EVENTS if off == want]
print('trace lines while processing block@%d : %d events' % (want, len(seq)))
print('LAST 30 in order:', seq[-30:])
ref = [ln for _f, ln, off in EVENTS if off == 0]
print('block@0 events=%d LAST 30: %s' % (len(ref), ref[-30:]))
print('only-in-14-lines:', sorted(set(seq) - set(ref)))
print('only-in-0-lines :', sorted(set(ref) - set(seq)))
