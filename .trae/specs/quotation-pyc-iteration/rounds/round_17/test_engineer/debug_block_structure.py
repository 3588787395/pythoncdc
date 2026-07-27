"""R17 调试：检查 load_get_index_stocks 的 CFG 块结构和角色"""
import sys
import dis
import importlib.util

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole

PYC = '/workspace/quotation.pyc'
module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

import types

def find_code(co, name):
    for const in co.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == name:
            return const
    return None

fn_code = find_code(code_obj, 'load_get_index_stocks')

# 构建 CFG
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(fn_code)

# 分析区域
ra = RegionAnalyzer(cfg)
ra.analyze()

# 列出所有块
print("=== CFG 块结构 ===")
_blocks = list(cfg.blocks.values()) if hasattr(cfg.blocks, 'values') else list(cfg.blocks)
for i, blk in enumerate(_blocks):
    role = ra.get_block_role(blk)
    region = ra.get_region_for_block(blk)
    last_instr = blk.instructions[-1] if blk.instructions else None
    print(f"  Block {i} (offset {blk.start_offset}): role={role}, "
          f"region={type(region).__name__ if region else 'None'}, "
          f"last={last_instr.opname if last_instr else 'None'}")
    if last_instr and last_instr.opname == 'POP_TOP':
        # 显示块内指令
        for ins in blk.instructions:
            print(f"    L{str(ins.starts_line or '-'):>3} {ins.offset:4d} {ins.opname:25s} {ins.argval!r}")
        # 显示后继
        print(f"    successors: {[b.start_offset for b in blk.successors]}")
        for s in blk.successors:
            s_role = ra.get_block_role(s)
            print(f"      successor {s.start_offset}: role={s_role}")
            for ins in s.instructions:
                print(f"        L{str(ins.starts_line or '-'):>3} {ins.offset:4d} {ins.opname:25s} {ins.argval!r}")
