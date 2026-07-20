"""Debug script for bool20_complex_logic boolop chain detection."""
import sys
import os
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, LoopRegion
from core.cfg.basic_block import BasicBlock


def analyze_source(src: str, label: str = ""):
    print(f"\n{'='*80}")
    print(f"=== {label} ===")
    print(f"Source: {src}")
    print('='*80)

    code = compile(src, '<test>', 'exec')
    cfg = CFGBuilder().build(code)

    print("\n--- Blocks ---")
    for blk in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
        last = blk.get_last_instruction()
        last_str = f"{last.opname}→{last.argval}" if last else "None"
        succs = [s.start_offset for s in blk.successors]
        cond_succs = [s.start_offset for s in blk.conditional_successors]
        print(f"  @{blk.start_offset}: last={last_str} succs={succs} cond_succs={cond_succs}")
        for ins in blk.instructions:
            print(f"    {ins.offset:4d} {ins.opname:30s} {ins.argval}")

    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    print("\n--- Regions ---")
    for r in analyzer.regions:
        blocks = sorted(b.start_offset for b in r.blocks) if hasattr(r, 'blocks') else []
        print(f"  {type(r).__name__}: blocks={blocks}")


if __name__ == '__main__':
    # bool04 - passes
    analyze_source("if a and b and c and d:\n    x = 1", "bool04 (passes)")

    # bool20 - fails
    analyze_source(
        "if (user and user.is_active() and (user.has_permission('read') or user.is_admin()) and resource.exists()):\n    access(resource)",
        "bool20 (fails)"
    )
