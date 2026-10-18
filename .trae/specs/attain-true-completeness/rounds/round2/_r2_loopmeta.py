#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 debug: dump LoopRegion metadata for a function.
usage: _r2_loopmeta.py <pyc> <fn>
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
from core.cfg.region_analyzer import LoopRegion

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
gen = RegionASTGenerator(cfg, top_level_code=None)
gen.region_analyzer.analyze()
for r in gen.region_analyzer.regions:
    if isinstance(r, LoopRegion):
        print('LoopRegion entry=@%s cond=@%s header=@%s' % (
            r.entry.start_offset if r.entry else None,
            r.condition_block.start_offset if r.condition_block else None,
            r.header_block.start_offset if r.header_block else None))
        print('  blocks=%s' % [b.start_offset for b in r.blocks])
        md = r.metadata or {}
        for k, v in sorted(md.items()):
            if isinstance(v, list):
                print('  md %s = %s' % (k, [getattr(x, 'start_offset', x) for x in v]))
            elif isinstance(v, (bool, int, str)):
                print('  md %s = %r' % (k, v))
            elif v is not None and hasattr(v, 'start_offset'):
                print('  md %s = @%s' % (k, v.start_offset))
            else:
                print('  md %s = %r' % (k, v))
        print('  cond_chain_blocks=%s' % [b.start_offset for b in (r.condition_chain_blocks or [])])
        print('  body_blocks=%s' % [b.start_offset for b in (getattr(r, 'body_blocks', None) or [])])
        print('  region_blocks=%s' % sorted(b.start_offset for b in (getattr(r, 'region_blocks', None) or [])))
