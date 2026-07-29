#!/usr/bin/env python3
"""Trace: check after-store logic for BoolOp@1862."""
import sys, types
sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, TernaryRegion

import core.cfg.region_ast_generator as mod
_orig_gbs = mod.RegionASTGenerator._generate_block_statements

def _traced_gbs(self, block, _cjb_parent=None):
    if block.start_offset == 2022:
        print(f"\n[GBS] _generate_block_statements(block@{block.start_offset})")
        print(f"  instructions: {[(i.opname, i.argval) for i in block.instructions if i.opname not in ('RESUME','NOP','CACHE','PUSH_NULL')]}")
    result = _orig_gbs(self, block, _cjb_parent)
    if block.start_offset == 2022:
        print(f"  result: {result}")
    return result

mod.RegionASTGenerator._generate_block_statements = _traced_gbs

m = load_pyc_file_v2('/workspace/quotation.pyc')
c = m.code.get() if hasattr(m.code, 'get') else m.code
if hasattr(c, 'to_python_code'):
    c = c.to_python_code()

from core.cfg.region_ast_generator import RegionASTGenerator
cfg = build_cfg(c)
gen = RegionASTGenerator(cfg, top_level_code=c if c.co_name == '<module>' else None)
ast_dict = gen.generate()
print("\n[TRACE] Done")
