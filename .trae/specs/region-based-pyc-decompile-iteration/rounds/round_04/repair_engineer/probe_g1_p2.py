# -*- coding: utf-8 -*-
"""Round 04 G1: dump P2 (while True + bare yield) 区域结构与 AST。"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, RegionType
from core.cfg.region_ast_generator import RegionASTGenerator

SRC = "def f():\n    while True:\n        i = 1\n        yield i\n"
code_obj = compile(SRC, "<p2>", "exec")
fn = [c for c in code_obj.co_consts if isinstance(c, type(code_obj))][0]
cfg = build_cfg(fn)

print("=== BLOCKS ===")
for bid, b in sorted(cfg.blocks.items()):
    ins = ", ".join(f"{i.opname}@{i.offset}" for i in b.instructions if i.opname != "CACHE")
    succ = sorted(s.start_offset for s in b.successors)
    print(f"block {bid} [{b.start_offset}]: {ins}  -> {succ}")

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print("\n=== REGIONS ===")


def walk(region, depth=0):
    indent = "  " * depth
    cls = type(region).__name__
    entry = region.entry.start_offset if getattr(region, "entry", None) else None
    blocks = sorted(b.start_offset for b in region.blocks) if hasattr(region, "blocks") and region.blocks else []
    print(f"{indent}{cls} entry={entry} blocks={blocks}")
    if isinstance(region, LoopRegion):
        print(f"{indent}  is_while_true={region.is_while_true} has_break={region.has_break} "
              f"body_blocks={[b.start_offset for b in region.body_blocks]}")
    for child in getattr(region, "children", []) or []:
        walk(child, depth + 1)


if not isinstance(regions, list):
    regions = [regions]
for r in regions:
    walk(r)

gen = RegionASTGenerator(cfg)
ast = gen.generate()
print("\n=== AST ===")
import json
print(json.dumps(ast, ensure_ascii=False, default=str)[:2000])
