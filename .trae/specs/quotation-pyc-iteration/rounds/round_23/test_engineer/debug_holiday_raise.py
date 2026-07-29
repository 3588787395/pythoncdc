"""R23-N19 调试 get_holiday_online 的区域分析（raise 在 if 分支中）"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, TryExceptRegion, LoopRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

target_co = None
for const in code_obj.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'get_holiday_online':
        target_co = const
        break

builder = CFGBuilder()
cfg = builder.build(target_co)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print(f"=== Regions ({len(analyzer.regions)}) ===")
for r in analyzer.regions:
    entry_off = r.entry.start_offset if r.entry else None
    merge_off = r.merge_block.start_offset if hasattr(r, 'merge_block') and r.merge_block else None
    print(f"  {type(r).__name__} entry={entry_off} merge={merge_off} parent={type(r.parent).__name__ if r.parent else None}")

# 找到包含 @428 的 IfRegion
print(f"\n=== 包含 @428 (load_count > 5) 的 IfRegion ===")
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry:
        if r.entry.start_offset == 418 or r.entry.start_offset == 420 or r.entry.start_offset == 422 or r.entry.start_offset == 428:
            print(f"  IfRegion entry={r.entry.start_offset} merge={r.merge_block.start_offset if r.merge_block else None}")
            if hasattr(r, 'then_blocks') and r.then_blocks:
                print(f"    then_blocks: {[b.start_offset for b in r.then_blocks]}")
                for b in r.then_blocks:
                    print(f"      block@{b.start_offset} instructions:")
                    for ins in b.instructions:
                        if ins.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                            _ar = getattr(ins, 'argrepr', ins.arg if ins.arg is not None else '')
                            print(f"        {ins.offset:4d} {ins.opname:30s} {_ar}")
            if hasattr(r, 'else_blocks') and r.else_blocks:
                print(f"    else_blocks: {[b.start_offset for b in r.else_blocks]}")

# 打印 TryExceptRegion 的详细信息
print(f"\n=== TryExceptRegion 详情 ===")
for r in analyzer.regions:
    if isinstance(r, TryExceptRegion):
        print(f"  TryExceptRegion entry={r.entry.start_offset}")
        print(f"  blocks: {[b.start_offset for b in r.blocks]}")
        if hasattr(r, 'try_blocks') and r.try_blocks:
            print(f"  try_blocks: {[b.start_offset for b in r.try_blocks]}")
        if hasattr(r, 'handlers') and r.handlers:
            print(f"  handlers ({len(r.handlers)}):")
            for h in r.handlers:
                print(f"    handler: {h}")
        if hasattr(r, 'except_blocks') and r.except_blocks:
            print(f"  except_blocks: {[b.start_offset for b in r.except_blocks]}")
        if hasattr(r, 'handler_blocks') and r.handler_blocks:
            print(f"  handler_blocks: {h}")
        # 打印所有属性
        for attr in dir(r):
            if not attr.startswith('_') and attr not in ('blocks', 'entry', 'parent', 'merge_block', 'instructions'):
                try:
                    val = getattr(r, attr)
                    if not callable(val):
                        if isinstance(val, list) and len(val) > 0 and hasattr(val[0], 'start_offset'):
                            print(f"  {attr}: {[b.start_offset for b in val]}")
                        elif isinstance(val, (str, int, float, bool, type(None))):
                            print(f"  {attr}: {val}")
                except:
                    pass

# 也打印 @428 所在块的完整信息
print(f"\n=== CFG 块 @428 ===")
for b in cfg.blocks.values():
    if b.start_offset == 428 or (b.start_offset <= 428 and getattr(b, 'end_offset', b.start_offset) >= 428):
        print(f"  block@{b.start_offset}-{getattr(b, 'end_offset', b.start_offset)}")
        for ins in b.instructions:
            if ins.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                _ar = getattr(ins, 'argrepr', ins.arg if ins.arg is not None else '')
                print(f"    {ins.offset:4d} {ins.opname:30s} {_ar}")
        print(f"  successors: {[s.start_offset for s in b.successors]}")
        break
