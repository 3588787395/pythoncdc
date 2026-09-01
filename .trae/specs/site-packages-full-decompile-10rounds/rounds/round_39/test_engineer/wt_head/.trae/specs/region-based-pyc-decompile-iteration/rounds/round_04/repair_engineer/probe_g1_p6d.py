# -*- coding: utf-8 -*-
"""Round 04 G1: dump P6 CFG + loop region blocks."""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SRC = "def f():\n    i = 0\n    while i < 10:\n        i += 1\n        yield i\n        yield i * 2\n"
code_obj = compile(SRC, "<p6>", "exec")
fn = [c for c in code_obj.co_consts if isinstance(c, type(code_obj))][0]

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
cfg = build_cfg(fn)
print("=== BLOCKS ===")
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    print(f"block@{b.start_offset}: {[i.opname for i in b.instructions]} -> succ={[s.start_offset for s in b.successors]}")

print("=== LOOP REGIONS ===")
ra = RegionAnalyzer(cfg)
ra.analyze()
for r in ra.regions:
    from core.cfg.region_analyzer import LoopRegion
    if isinstance(r, LoopRegion):
        print(f"LoopRegion entry={r.entry.start_offset if r.entry else None}")
        print(f"  header_block={r.header_block.start_offset if r.header_block else None}")
        print(f"  condition_block={r.condition_block.start_offset if r.condition_block else None}")
        print(f"  natural_back_edge={r.natural_back_edge.start_offset if r.natural_back_edge else None}")
        print(f"  blocks={[b.start_offset for b in r.blocks]}")
        print(f"  back_edge_source_blocks={[(b.start_offset, n) for b, n in (r.back_edge_source_blocks or [])]}")
        print(f"  body_blocks={[b.start_offset for b in (r.body_blocks or [])]}")
