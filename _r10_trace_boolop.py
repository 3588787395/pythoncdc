#!/usr/bin/env python3
"""Trace: patch _generate_boolop to see which BoolOpRegions are generated."""
import sys, types
sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, TernaryRegion

import core.cfg.region_ast_generator as mod
_orig_boolop = mod.RegionASTGenerator._generate_boolop

def _traced_boolop(self, region, skip_store_targets=None):
    entry_off = region.entry.start_offset if region.entry else None
    merge_off = region.merge_block.start_offset if region.merge_block else None
    if entry_off and 1680 <= entry_off <= 2090:
        print(f"\n[BOOLOP] _generate_boolop entry={entry_off} merge={merge_off} val_tgt={region.value_target}")
        print(f"  blocks before: entry_in_gen={region.entry in self.generated_blocks}")
    result = _orig_boolop(self, region, skip_store_targets)
    if entry_off and 1680 <= entry_off <= 2090:
        print(f"  result stmts: {[s.get('type') for s in result] if result else None}")
        print(f"  blocks after: entry_in_gen={region.entry in self.generated_blocks}")
        # Check if merge_block 1862 is now generated
        blk_1862 = self.cfg.get_block_by_offset(1862)
        if blk_1862:
            print(f"  blk@1862 in generated: {blk_1862 in self.generated_blocks}")
        # Check if BoolOp@1862 entry is now generated
        for _r in self.regions:
            if isinstance(_r, BoolOpRegion) and _r.entry and _r.entry.start_offset == 1862 and _r is not region:
                print(f"  BoolOp@1862 entry_in_gen={_r.entry in self.generated_blocks}")
    return result

mod.RegionASTGenerator._generate_boolop = _traced_boolop

# Also trace the children loop skip
_orig_then = mod.RegionASTGenerator._if_generate_then_branch
def _traced_then(self, region):
    if region.entry and region.entry.start_offset == 1686:
        print(f"\n[THEN] _if_generate_then_branch IfRegion@{region.entry.start_offset}")
    return _orig_then(self, region)
mod.RegionASTGenerator._if_generate_then_branch = _traced_then

m = load_pyc_file_v2('/workspace/quotation.pyc')
c = m.code.get() if hasattr(m.code, 'get') else m.code
if hasattr(c, 'to_python_code'):
    c = c.to_python_code()

from core.cfg.region_ast_generator import RegionASTGenerator

cfg = build_cfg(c)
gen = RegionASTGenerator(cfg, top_level_code=c if c.co_name == '<module>' else None)
ast_dict = gen.generate()
print("\n[TRACE] Done")
