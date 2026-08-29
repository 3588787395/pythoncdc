# -*- coding: utf-8 -*-
"""Round 04 G1: 追踪 P6 body 块语句生成路径。"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion
from core.cfg.region_ast_generator import RegionASTGenerator

SRC = "def f():\n    i = 0\n    while i < 10:\n        i += 1\n        yield i\n        yield i * 2\n"
code_obj = compile(SRC, "<p6>", "exec")
fn = [c for c in code_obj.co_consts if isinstance(c, type(code_obj))][0]
cfg = build_cfg(fn)

print("=== BLOCKS ===")
for bid, b in sorted(cfg.blocks.items()):
    ins = ", ".join(f"{i.opname}@{i.offset}" for i in b.instructions if i.opname != "CACHE")
    succ = sorted(s.start_offset for s in b.successors)
    print(f"block {bid} [{b.start_offset}]: {ins}  -> {succ}")

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()


def walk(region, depth=0):
    indent = "  " * depth
    cls = type(region).__name__
    entry = region.entry.start_offset if getattr(region, "entry", None) else None
    blocks = sorted(b.start_offset for b in region.blocks) if hasattr(region, "blocks") and region.blocks else []
    extra = ""
    if isinstance(region, LoopRegion):
        cb = region.condition_block.start_offset if region.condition_block else None
        be = region.back_edge_block.start_offset if region.back_edge_block else None
        extra = f" cond={cb} backedge={be} body={[b.start_offset for b in region.body_blocks]}"
    print(f"{indent}{cls} entry={entry} blocks={blocks}{extra}")
    for child in getattr(region, "children", []) or []:
        walk(child, depth + 1)


print("\n=== REGIONS ===")
if not isinstance(regions, list):
    regions = [regions]
for r in regions:
    walk(r)
