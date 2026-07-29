"""R23-N19: 调试 get_holiday_online 的区域分析"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# 找到 get_holiday_online 的 code object
import types
target_co = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'get_holiday_online':
        target_co = const
        break

print(f"Found: {target_co.co_name}")

# 构建 CFG
builder = CFGBuilder()
cfg = builder.build(target_co)

print(f"\n=== CFG Blocks ===")
for key in sorted(cfg.blocks.keys(), key=lambda k: cfg.blocks[k].start_offset if hasattr(cfg.blocks[k], 'start_offset') else k):
    b = cfg.blocks[key]
    b_off = b.start_offset if hasattr(b, 'start_offset') else key
    succs = [s.start_offset for s in b.successors]
    preds = [p.start_offset for p in b.predecessors]
    last_instr = b.instructions[-1] if b.instructions else None
    last_str = f"{last_instr.opname} {getattr(last_instr, 'argrepr', last_instr.arg)}" if last_instr else "empty"
    first_str = f"{b.instructions[0].opname}" if b.instructions else "empty"
    print(f"  @{b_off:4d} (key={key}) first={first_str} succs={succs} preds={preds} last={last_str}")

# 区域分析
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print(f"\n=== Regions ===")
for r in analyzer.regions:
    entry_off = r.entry.start_offset if r.entry else None
    blocks = [b.start_offset for b in r.blocks]
    merge_off = r.merge_block.start_offset if getattr(r, 'merge_block', None) else None
    print(f"  {r.region_type.name} entry=@{entry_off} blocks={blocks} merge=@{merge_off}")
    if hasattr(r, 'then_blocks') and r.then_blocks:
        print(f"    then_blocks={[b.start_offset for b in r.then_blocks]}")
    if hasattr(r, 'else_blocks') and r.else_blocks:
        print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")
    if hasattr(r, 'elif_conditions') and r.elif_conditions:
        print(f"    elif_conditions={len(r.elif_conditions)}")
    if hasattr(r, 'elif_bodies') and r.elif_bodies:
        print(f"    elif_bodies={[ [b.start_offset for b in eb] for eb in r.elif_bodies]}")
    if hasattr(r, 'elif_final_else') and r.elif_final_else:
        print(f"    elif_final_else={[b.start_offset for b in r.elif_final_else]}")
    if hasattr(r, 'handler_blocks') and r.handler_blocks:
        print(f"    handler_blocks={[b.start_offset for b in r.handler_blocks]}")
    if hasattr(r, 'else_handler_blocks') and r.else_handler_blocks:
        print(f"    else_handler_blocks={[b.start_offset for b in r.else_handler_blocks]}")
