#!/usr/bin/env python3
"""Trace: confirm BoolOpRegion@1862 is skipped in _if_generate_then_branch children loop."""
import sys, types
sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, TernaryRegion

# Monkey-patch _if_generate_then_branch to trace children loop
import core.cfg.region_ast_generator as mod
_orig = mod.RegionASTGenerator._if_generate_then_branch

def _traced(self, region):
    if region.entry and region.entry.start_offset == 1686:
        print(f"\n[TRACE] _if_generate_then_branch for IfRegion@{region.entry.start_offset}")
        print(f"  children: {[(type(c).__name__, c.entry.start_offset if getattr(c, 'entry', None) else None) for c in (region.children or [])]}")
        print(f"  then_blocks: {[b.start_offset for b in (region.then_blocks or [])]}")
        for child in (region.children or []):
            if not isinstance(child, (BoolOpRegion, TernaryRegion)):
                print(f"  child {type(child).__name__}: not BoolOp/Ternary → skip")
                continue
            if not hasattr(child, 'entry') or child.entry is None:
                print(f"  child {type(child).__name__}: no entry → skip")
                continue
            entry_gen = child.entry in self.generated_blocks
            child_gen = id(child) in self._generated_regions
            print(f"  child BoolOp@{child.entry.start_offset}: entry_in_generated={entry_gen} child_in_generated_regions={child_gen}")
            if entry_gen:
                # Check dual-role
                for _r in self.regions:
                    if (isinstance(_r, BoolOpRegion) and _r is not child
                            and _r.merge_block is child.entry
                            and id(_r) in self._generated_regions):
                        print(f"    -> DUAL-ROLE: entry {child.entry.start_offset} is merge of BoolOp@{_r.entry.start_offset} (already generated)")
                        break
    return _orig(self, region)

mod.RegionASTGenerator._if_generate_then_branch = _traced

m = load_pyc_file_v2('/workspace/quotation.pyc')
c = m.code.get() if hasattr(m.code, 'get') else m.code
if hasattr(c, 'to_python_code'):
    c = c.to_python_code()

from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

cfg = build_cfg(c)
gen = RegionASTGenerator(cfg, top_level_code=c if c.co_name == '<module>' else None)
ast_dict = gen.generate()
print("\n[TRACE] Generation complete")
