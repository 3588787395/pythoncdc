#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 item14 debug: dump blocks + regions for a given function in a pyc.
usage: _r2_b78trace.py <pyc> <fn>
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


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


pyc = sys.argv[1]
name = sys.argv[2]
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])
targets = []
find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
gen.region_analyzer.analyze()

print('==== %s ==== co_name=%s' % (name, co.co_name))
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    ins = ', '.join('%d:%s%s' % (
        i.offset, i.opname,
        ('->%s' % i.argval) if i.argval is not None and
        ('JUMP' in i.opname or i.opname.startswith('POP_JUMP')) else
        ('(%r)' % (i.argval,) if i.argval is not None else ''))
        for i in b.instructions)
    print('@%d  [%s]' % (b.start_offset, ins))
print('---- regions ----')
for r in gen.region_analyzer.regions:
    bl = ','.join(str(x.start_offset) for x in (r.blocks or []))
    extra = ''
    for attr in ('condition_block', 'merge_block', 'entry', 'header_block'):
        v = getattr(r, attr, None)
        if v is not None:
            extra += ' %s=@%s' % (attr, v.start_offset)
    eb = getattr(r, 'else_blocks', None)
    if eb:
        extra += ' else=' + ','.join(str(x.start_offset) for x in eb)
    print('  %-14s blocks=[%s]%s' % (type(r).__name__, bl, extra))
