"""Debug: check chained compare operands for is_listing."""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
import marshal, dis, types

pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQEngine/core/asset.pyc"
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name, results=None):
    if results is None: results = []
    if code_obj.co_name == name: results.append(code_obj)
    for c in code_obj.co_consts:
        if isinstance(c, types.CodeType): find_code(c, name, results)
    return results

listings = find_code(code, 'is_listing')
target_co = None
for co in listings:
    instrs = list(dis.get_instructions(co))
    if any(i.opname == 'JUMP_IF_FALSE_OR_POP' for i in instrs):
        target_co = co
        break

cfg = build_cfg(target_co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

for r in regions:
    if type(r).__name__ == 'IfRegion' and getattr(r, 'chained_compare_ops', None):
        print(f"IfRegion: chained_compare_ops={r.chained_compare_ops}")
        print(f"  chained_compare_blocks: {[b.start_offset for b in r.chained_compare_blocks]}")
        print(f"  chained_left_instr: {r.chained_left_instr}")
        if r.chained_left_instr:
            print(f"    opname={r.chained_left_instr.opname}, argval={getattr(r.chained_left_instr, 'argval', '?')}")
        print(f"  chained_comparator_instrs:")
        for ci in r.chained_comparator_instrs:
            print(f"    opname={ci.opname}, argval={getattr(ci, 'argval', '?')}")
        
        # Show all blocks' instructions
        all_blocks = [r.condition_block] + list(r.chained_compare_blocks)
        for i, block in enumerate(all_blocks):
            print(f"\n  block[{i}] @ {block.start_offset}:")
            for instr in block.instructions:
                argval = getattr(instr, 'argval', '')
                print(f"    {instr.offset:4d}  {instr.opname:<30} arg={instr.arg} argval={argval}")
