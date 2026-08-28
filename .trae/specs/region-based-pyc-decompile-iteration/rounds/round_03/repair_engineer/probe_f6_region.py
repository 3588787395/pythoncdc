# -*- coding: utf-8 -*-
"""F6 probe: check whether LoopRegion.else_blocks survives region analysis for repro_02."""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")

SRC = (
    "def f(items):\n"
    "    for i in items:\n"
    "        if i > 0:\n"
    "            break\n"
    "    else:\n"
    "        return None\n"
    "    return i\n"
)

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

code_obj = compile(SRC, "<f6>", "exec")
fn = [c for c in code_obj.co_consts if isinstance(c, type(code_obj))][0]
cfg = build_cfg(fn)

print("=== CFG blocks ===")
for bid, b in sorted(cfg.blocks.items()):
    ins = ", ".join(f"{i.opname}@{i.offset}" for i in b.instructions if i.opname != "CACHE")
    succ = sorted(s.start_offset for s in b.successors)
    print(f"block {bid} [{b.start_offset}]: {ins}  -> {succ}")

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print("\n=== LoopRegions ===")


def walk(region, depth=0):
    indent = "  " * depth
    if isinstance(region, LoopRegion):
        eb = getattr(region, "else_blocks", None)
        fie = region.metadata.get("for_iter_exit")
        print(f"{indent}LoopRegion type={region.region_type}, entry={region.entry.start_offset}, "
              f"has_break={region.has_break}, else_is_follow={region.else_is_follow}")
        print(f"{indent}  else_blocks={[b.start_offset for b in eb] if eb else None}")
        print(f"{indent}  break_blocks={[b.start_offset for b in region.break_blocks]}")
        print(f"{indent}  for_iter_exit={fie.start_offset if fie else None}")
        print(f"{indent}  blocks={sorted(b.start_offset for b in region.blocks)}")
    for child in getattr(region, "children", []) or []:
        walk(child, depth + 1)


if not isinstance(regions, list):
    regions = [regions]
for r in regions:
    walk(r)
