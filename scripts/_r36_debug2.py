import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
import marshal
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, LoopRegion
from core.cfg.region_ast_generator import RegionASTGenerator, RegionType, SHORT_CIRCUIT_JUMP_OPS

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

# Check the BoolOpRegion's op_chain blocks vs IfRegion's merge_block
for r in regions:
    if isinstance(r, BoolOpRegion) and r.entry and r.entry.start_offset == 152:
        print(f"BoolOpRegion entry=152:")
        for cb, op in r.op_chain:
            print(f"  chain_block: offset={cb.start_offset}, id={id(cb)}")
        print(f"  merge_block: offset={r.merge_block.start_offset if r.merge_block else None}")

        # Check IfRegions with merge_block == chain_block
        for chain_block, _ in r.op_chain:
            print(f"\n  Looking for IfRegion with merge_block is chain_block(offset={chain_block.start_offset}, id={id(chain_block)}):")
            for r2 in regions:
                if isinstance(r2, IfRegion):
                    mb = getattr(r2, 'merge_block', None)
                    if mb is not None:
                        print(f"    IfRegion(entry={r2.entry.start_offset}): merge_block offset={mb.start_offset}, id={id(mb)}, is_chain={mb is chain_block}")

# Now try to build the expression
print("\n=== Trying _build_boolop_expression ===")
for r in regions:
    if isinstance(r, BoolOpRegion) and r.entry and r.entry.start_offset == 152:
        expr = gen._build_boolop_expression(r)
        print(f"Result: {expr}")
        if expr is None:
            print("FAILED: expression is None")
            # Try manually
            for cb, op in r.op_chain:
                print(f"\n  chain_block {cb.start_offset} (op={op}):")
                result = gen._try_build_chained_compare_in_boolop(cb, r)
                print(f"    _try_build_chained_compare_in_boolop: {result}")
