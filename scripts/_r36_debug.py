import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
import marshal
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, LoopRegion
from core.cfg.region_ast_generator import RegionASTGenerator, RegionType

f = open('site-packages/IQEngine/utils/trade_schedule.pyc','rb')
f.read(16)
co = marshal.load(f)

for c in co.co_consts:
    if hasattr(c, 'co_code') and c.co_name == 'is_stock_trade_time_now':
        target_co = c
        break

cfg = CFGBuilder().build(target_co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

gen = RegionASTGenerator(cfg)
gen.regions = regions
gen.region_analyzer = analyzer

# Check top_level filtering
top_level = [r for r in regions if r.parent is None]
print(f"Top-level regions ({len(top_level)}):")
for r in top_level:
    print(f"  {type(r).__name__} (entry={r.entry.start_offset if r.entry else None})")
    if isinstance(r, BoolOpRegion):
        print(f"    op_chain: {[(b.start_offset, op) for b, op in r.op_chain]}")
        print(f"    merge_block: {r.merge_block.start_offset if r.merge_block else None}")
        # Check _is_outer_condition
        _enclosing = r.find_enclosing_parent((LoopRegion, IfRegion))
        print(f"    enclosing: {type(_enclosing).__name__ if _enclosing else None}")
        if _enclosing:
            print(f"    enclosing.condition_block: {_enclosing.condition_block.start_offset if _enclosing.condition_block else None}")
            print(f"    enclosing.entry: {_enclosing.entry.start_offset if _enclosing.entry else None}")
            # Check if any chain block matches enclosing.condition_block
            for cb, _ in r.op_chain:
                if cb == _enclosing.condition_block:
                    print(f"    MATCH: chain_block {cb.start_offset} == enclosing.condition_block")
        # Check merge_block successor
        if r.merge_block:
            mb_last = r.merge_block.get_last_instruction()
            print(f"    merge_block.last: {mb_last.opname if mb_last else None}")
            for ms in r.merge_block.successors:
                ms_last = ms.get_last_instruction()
                print(f"    merge_block.successor {ms.start_offset}: last={ms_last.opname if ms_last else None}")

# Now try generating
print("\n=== Generating ===")
result = gen.generate()
print(f"\nResult body:")
for stmt in result.get('body', []):
    print(f"  {stmt}")
