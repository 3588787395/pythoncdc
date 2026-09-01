"""R28 测试工程师：调试share_change的区域识别"""
import sys
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# 找到share_change的code object
share_change_co = None
for const in code_obj.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'share_change':
        share_change_co = const
        break

print(f"share_change co: {share_change_co}")

# 构建CFG
builder = CFGBuilder()
cfg = builder.build(share_change_co)

print(f"\n=== Blocks (共{len(cfg.blocks)}) ===")
for blk in cfg.get_blocks_in_order():
    last = blk.get_last_instruction()
    last_str = f"{last.opname}→{last.argval}" if last else "None"
    print(f"  blk@{blk.start_offset}: last={last_str}, succs={[s.start_offset for s in blk.successors]}")

# 分析区域
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print(f"\n=== Regions (共{len(regions)}) ===")
for r in regions:
    blocks_str = [b.start_offset for b in r.blocks]
    print(f"  {type(r).__name__}: entry={r.entry.start_offset}, blocks={blocks_str}")
    if hasattr(r, 'op_chain'):
        print(f"    op_chain: {[(b.start_offset, op) for b, op in r.op_chain]}")
    if hasattr(r, 'then_blocks') and r.then_blocks:
        print(f"    then_blocks: {[b.start_offset for b in r.then_blocks]}")
    if hasattr(r, 'else_blocks') and r.else_blocks:
        print(f"    else_blocks: {[b.start_offset for b in r.else_blocks]}")
    if hasattr(r, 'merge_block') and r.merge_block:
        print(f"    merge_block: {r.merge_block.start_offset}")
