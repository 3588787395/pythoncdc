"""R24-N1 调试：检查 valuation 块 724 的内容（被标记为 break 但可能是 return）"""
import sys
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
from core.pyc_loader_v2 import load_pyc_file_v2

module = load_pyc_file_v2('/workspace/quotation.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

import types
def find_func(co, name):
    if co.co_name == name:
        return co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            result = find_func(const, name)
            if result:
                return result
    return None

val_co = find_func(code_obj, 'valuation')

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(val_co)

# Check block 724
for block in cfg.blocks.values():
    if block.start_offset == 724:
        print(f"Block 724:")
        print(f"  instructions:")
        for ins in block.instructions:
            print(f"    {ins.offset:4d} {ins.opname:30s} {getattr(ins, 'argval', '')} {getattr(ins, 'argrepr', '')}")
        print(f"  successors: {[s.start_offset for s in block.successors]}")
        print(f"  predecessors: {[p.start_offset for p in block.predecessors]}")
        # Check block role
        analyzer = RegionAnalyzer(cfg)
        analyzer.analyze()
        role = analyzer.get_block_role(block)
        print(f"  block_role: {role}")
        break

# Also check the LoopRegion@520 break_blocks detection
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()
for r in analyzer.regions:
    if r.__class__.__name__ == 'LoopRegion' and r.entry and r.entry.start_offset == 520:
        print(f"\nLoopRegion@520:")
        print(f"  has_break: {getattr(r, 'has_break', 'NOT SET')}")
        print(f"  break_blocks: {[b.start_offset for b in getattr(r, 'break_blocks', [])]}")
        for bb in getattr(r, 'break_blocks', []):
            print(f"    break_block {bb.start_offset}:")
            last = bb.get_last_instruction()
            print(f"      last instr: {last.opname if last else 'None'} {last.argrepr if last else ''}")
            # Check if it's a RETURN
            has_return = any(i.opname == 'RETURN_VALUE' for i in bb.instructions)
            has_jump_forward = any(i.opname == 'JUMP_FORWARD' for i in bb.instructions)
            print(f"      has RETURN_VALUE: {has_return}")
            print(f"      has JUMP_FORWARD: {has_jump_forward}")
        break
