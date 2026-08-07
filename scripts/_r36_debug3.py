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
gen = RegionASTGenerator(cfg)
result = gen.generate()

print("=== Generated body ===")
for i, stmt in enumerate(result.get('body', [])):
    print(f"  [{i}] type={stmt.get('type')} ", end='')
    if stmt.get('type') == 'If':
        test = stmt.get('test', {})
        print(f"test_type={test.get('type')}")
    elif stmt.get('type') == 'Return':
        val = stmt.get('value', {})
        print(f"value_type={val.get('type')}")
    else:
        print()

print("\n=== Generated blocks ===")
for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    print(f"  block {block.start_offset}: generated={block in gen.generated_blocks}")
