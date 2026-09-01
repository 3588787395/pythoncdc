"""R17 调试：检查 Block 6 和 Block 7 的角色和区域归属"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole


PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}

    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)

    walk(code_obj)
    return result


codes = load_pyc_code_objects(PYC)
f_code = codes['load_get_index_stocks']

cfg = build_cfg(f_code)
ra = RegionAnalyzer(cfg)
ra.analyze()

_blocks = list(cfg.blocks.values()) if hasattr(cfg.blocks, 'values') else list(cfg.blocks)
for i, blk in enumerate(_blocks):
    role = ra.get_block_role(blk)
    region = ra.get_region_for_block(blk)
    last_instr = blk.instructions[-1] if blk.instructions else None
    print(f"  Block {i} (offset {blk.start_offset}): role={role}, "
          f"region={type(region).__name__ if region else 'None'}, "
          f"last={last_instr.opname if last_instr else 'None'}")
    if i in (6, 7):
        # 显示前驱和后继
        print(f"    predecessors: {[b.start_offset for b in blk.predecessors]}")
        print(f"    successors: {[b.start_offset for b in blk.successors]}")
        # 显示块内指令
        for ins in blk.instructions:
            print(f"    L{str(ins.starts_line or '-'):>3} {ins.offset:4d} {ins.opname:25s} {ins.argval!r}")

# 列出所有区域
print(f"\n=== 所有区域 ===")
for r in ra.regions:
    print(f"  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}, "
          f"blocks={[b.start_offset for b in r.blocks]}")
    if hasattr(r, 'then_blocks'):
        print(f"    then_blocks={[b.start_offset for b in (r.then_blocks or [])]}")
    if hasattr(r, 'else_blocks'):
        print(f"    else_blocks={[b.start_offset for b in (r.else_blocks or [])]}")
    if hasattr(r, 'merge_block') and r.merge_block:
        print(f"    merge_block={r.merge_block.start_offset}")
