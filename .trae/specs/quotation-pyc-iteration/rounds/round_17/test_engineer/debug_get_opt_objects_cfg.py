"""R17 调试 get_opt_objects 的 CFG 和区域结构"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole

PYC = '/workspace/quotation.pyc'
module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find_code(co, name):
    for const in co.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == name:
            return const
    return None

fn_code = find_code(code_obj, 'get_opt_objects')

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(fn_code)

ra = RegionAnalyzer(cfg)
ra.analyze()

print("=== CFG 块结构 ===")
_blocks = list(cfg.blocks.values()) if hasattr(cfg.blocks, 'values') else list(cfg.blocks)
for i, blk in enumerate(_blocks):
    role = ra.get_block_role(blk)
    region = ra.get_region_for_block(blk)
    last_instr = blk.instructions[-1] if blk.instructions else None
    print(f"  Block {i} (offset {blk.start_offset}): role={role}, "
          f"region={type(region).__name__ if region else 'None'}, "
          f"last={last_instr.opname if last_instr else 'None'}")
    for ins in blk.instructions:
        print(f"    L{str(ins.starts_line or '-'):>3} {ins.offset:4d} {ins.opname:25s} {ins.argval!r}")

print("\n=== 区域列表 ===")
for r in ra.regions:
    print(f"  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}, "
          f"blocks={[b.start_offset for b in r.blocks]}")
