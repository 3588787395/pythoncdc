#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 item14 debug: trace top-level region dispatch for a function.
usage: _r2_b78dispatch.py <pyc> <fn>
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
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, Region

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

_orig_gen_region = RegionASTGenerator._generate_region
_orig_gen_if = RegionASTGenerator._generate_if


def traced_gen_region(self, region, skip_store_targets=None):
    r = _orig_gen_region(self, region, skip_store_targets)
    print('[dispatch] %-14s entry=@%s -> %s' % (
        type(region).__name__,
        region.entry.start_offset if region.entry else None,
        ('None' if r is None else
         ('list[%d]' % len(r) if isinstance(r, list) else r.get('type')))))
    return r


def traced_gen_if(self, region):
    print('[_generate_if] entry=@%s cond=@%s merge=@%s blocks=%s' % (
        region.entry.start_offset if region.entry else None,
        region.condition_block.start_offset if region.condition_block else None,
        region.merge_block.start_offset if region.merge_block else None,
        [b.start_offset for b in (region.blocks or [])]))
    r = _orig_gen_if(self, region)
    print('[_generate_if] entry=@%s -> %s' % (
        region.entry.start_offset if region.entry else None,
        ('None' if r is None else
         ('list[%d]' % len(r) if isinstance(r, list) else r.get('type')))))
    return r


RegionASTGenerator._generate_region = traced_gen_region
RegionASTGenerator._generate_if = traced_gen_if
ast = gen.generate()
print('==== final AST body ====')
for s in (ast.get('body') or []):
    print('  ', s.get('type'))
print('generated blocks:',
      sorted(b.start_offset for b in gen.generated_blocks))
