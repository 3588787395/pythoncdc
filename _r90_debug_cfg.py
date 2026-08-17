#!/usr/bin/env python3
"""R90 深入分析 get_kline_by_count_new 的 CFG 结构"""

import sys
import os
import dis
import marshal
import types

sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')

from pycdc import decompile_pyc as _pycdc_decompile
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"

# 加载原始 pyc
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

# 找到 get_kline_by_count_new
def find_function(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            inner = find_function(const, name)
            if inner:
                return inner
    return None

func_code = find_function(orig_code, 'get_kline_by_count_new')
if not func_code:
    print("函数未找到!")
    sys.exit(1)

print(f"函数: {func_code.co_name}")
print(f"参数: {func_code.co_varnames[:func_code.co_argcount]}")
print(f"字节码长度: {len(func_code.co_code)}")

# 打印前 50 条指令
print("\n前 50 条指令:")
for i, instr in enumerate(dis.get_instructions(func_code)):
    if i >= 50:
        break
    print(f"  {i:3d} {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")

# 构建 CFG
builder = CFGBuilder()
cfg = builder.build(func_code)

print(f"\nCFG 基本块数: {len(cfg.blocks)}")
for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    instrs = [i for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
    if not instrs:
        continue
    print(f"\n  Block @offset={block.start_offset}:")
    for instr in instrs[:15]:
        _arg = getattr(instr, 'argval', getattr(instr, 'arg', ''))
        print(f"    {instr.offset:4d} {instr.opname:30s} {_arg}")
    if len(instrs) > 15:
        print(f"    ... ({len(instrs) - 15} more)")
    print(f"    successors: {[s.start_offset for s in block.successors]}")

# 分析区域
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
print(f"\n区域数: {len(regions)}")
for region in regions:
    print(f"  {type(region).__name__}: entry={region.entry_block.start_offset if hasattr(region, 'entry_block') else '?'}")