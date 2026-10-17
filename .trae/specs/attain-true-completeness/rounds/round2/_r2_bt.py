#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: trace _detect_boolop_conditional_chain calls during analyze() for one fn.
usage: _r2_bt.py <pyc> <name>
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

orig = RegionAnalyzer._detect_boolop_conditional_chain
log = []


def patched(self, start_block, claimed, skip_claimed_check=False, try_scope_exempt=False):
    res = orig(self, start_block, claimed, skip_claimed_check, try_scope_exempt)
    log.append((start_block.start_offset, skip_claimed_check, try_scope_exempt,
                None if res is None else [(b.start_offset, o) for b, o in res],
                len(claimed)))
    return res


RegionAnalyzer._detect_boolop_conditional_chain = patched
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
analyzer = gen.region_analyzer
analyzer.analyze()
print('---- _detect_boolop_conditional_chain calls ----')
for start, sk, ts, res, ncl in log:
    print('  start=@%d skip=%s try_exempt=%s claimed_n=%d -> %s' % (start, sk, ts, ncl, res))
print('---- final regions ----')
for r in analyzer.regions:
    print('  %s entry=@%s type=%s' % (type(r).__name__, r.entry.start_offset,
                                      getattr(r, 'region_type', '')))
