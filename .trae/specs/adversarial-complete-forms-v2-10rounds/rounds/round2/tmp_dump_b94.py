"""Temporary diagnostic: dump CFG blocks + loops for a given function of a pyc."""
import sys, marshal, dis
import types as _types

sys.path.insert(0, r"F:\Downloads\pythoncdc-main")

f = open(r"F:\Downloads\pythoncdc-main\test_repros\round2\x01_if_deep_hosts.pyc", 'rb')
f.read(16)
module_code = marshal.load(f)

FUNC = sys.argv[1] if len(sys.argv) > 1 else 'if_in_while'

target = None
for const in module_code.co_consts:
    if hasattr(const, 'co_name') and const.co_name == FUNC:
        target = const
        break
if target is None:
    print("function not found", FUNC)
    sys.exit(1)

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion
from core.cfg.dominator_analyzer import LoopAnalyzer

cfg = build_cfg(target)
print("=== BLOCKS ===")
for off in sorted(cfg.blocks):
    b = cfg.blocks[off]
    last = b.get_last_instruction()
    succs = [s.start_offset for s in b.successors]
    preds = [p.start_offset for p in b.predecessors]
    ops = [(i.offset, i.opname) for i in b.instructions]
    print(f"B{off}: ops={ops} last={last.opname if last else None} succ={succs} pred={preds}")

analyzer = RegionAnalyzer(cfg)
analyzer.dom_analyzer.analyze()
analyzer.loop_analyzer = LoopAnalyzer(cfg, analyzer.dom_analyzer)
analyzer.loop_analyzer.analyze()
analyzer._coalesce_nop_prefix_loop_headers()

print("=== LOOPS (loop_analyzer) ===")
for header, loops in analyzer.loop_analyzer.get_all_loops().items():
    print(f"header B{header.start_offset}:")
    for lp in loops:
        print("   loop obj:", lp)

print("=== BACK EDGES ===")
print([(s.start_offset, t.start_offset) for s, t in analyzer.loop_analyzer.back_edges])

regions = analyzer._identify_loop_regions()
print("=== LOOP REGIONS (after identify) ===")
def show(r, indent="  "):
    print(indent, type(r).__name__,
          "blocks=", sorted(b.start_offset for b in r.blocks),
          "header=", r.header_block.start_offset if getattr(r, 'header_block', None) else None,
          "cond=", r.condition_block.start_offset if getattr(r, 'condition_block', None) else None,
          "body=", sorted(b.start_offset for b in (getattr(r, 'body_blocks', None) or [])),
          "else=", sorted(b.start_offset for b in (getattr(r, 'else_blocks', None) or [])),
          "while_true=", getattr(r, 'is_while_true', None))
    for c in getattr(r, 'children', None) or []:
        show(c, indent + "    ")
for r in regions:
    show(r)

print("=== FULL analyze() ===")
analyzer2 = RegionAnalyzer(cfg)
all_regions = analyzer2.analyze()
print("total regions:", len(all_regions))
for r in all_regions:
    show(r, "  ")
print("=== block_to_region ===")
for off in sorted(analyzer2.block_to_region, key=lambda b: b.start_offset):
    print(f"  B{off.start_offset} -> {type(analyzer2.block_to_region[off]).__name__}")
print("=== block_roles ===")
for off in sorted(analyzer2.block_roles):
    print(f"  B{off} -> {analyzer2.block_roles[off]}")
