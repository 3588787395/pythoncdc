"""R23-N19 调试 share_change 的区域分析结果"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# 找到 share_change
target_co = None
for const in code_obj.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'share_change':
        target_co = const
        break

print(f"Found share_change: {target_co is not None}")

builder = CFGBuilder()
cfg = builder.build(target_co)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print(f"\n=== Regions ({len(analyzer.regions)}) ===")
for r in analyzer.regions:
    print(f"  {type(r).__name__} entry={r.entry.start_offset if r.entry else None} parent={type(r.parent).__name__ if r.parent else None}")

print(f"\n=== BoolOpRegions ===")
for r in analyzer.regions:
    if isinstance(r, BoolOpRegion):
        print(f"  BoolOpRegion entry={r.entry.start_offset} merge={r.merge_block.start_offset if r.merge_block else None}")
        print(f"    op_chain ({len(r.op_chain)}):")
        for i, (blk, op) in enumerate(r.op_chain):
            last = blk.get_last_instruction()
            last_str = f"{last.opname} -> {last.argval}" if last else "(none)"
            print(f"      [{i}] block@{blk.start_offset} op={op} last={last_str}")
            for ins in blk.instructions:
                if ins.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                    continue
                _ar = getattr(ins, 'argrepr', ins.arg if ins.arg is not None else '')
                print(f"          {ins.offset:4d} {ins.opname:30s} {_ar}")

print(f"\n=== IfRegions ===")
for r in analyzer.regions:
    if isinstance(r, IfRegion):
        print(f"  IfRegion entry={r.entry.start_offset} merge={r.merge_block.start_offset if r.merge_block else None}")
        if hasattr(r, 'then_blocks') and r.then_blocks:
            print(f"    then_blocks: {[b.start_offset for b in r.then_blocks]}")
        if hasattr(r, 'else_blocks') and r.else_blocks:
            print(f"    else_blocks: {[b.start_offset for b in r.else_blocks]}")
        # 打印条件块指令
        cb = r.entry
        print(f"    cond_block@{cb.start_offset}:")
        for ins in cb.instructions:
            if ins.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            _ar = getattr(ins, 'argrepr', ins.arg if ins.arg is not None else '')
            print(f"      {ins.offset:4d} {ins.opname:30s} {_ar}")
