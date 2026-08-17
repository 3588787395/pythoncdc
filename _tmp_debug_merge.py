"""Debug: check merge_block instructions for is_listing."""
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
    if type(r).__name__ == 'IfRegion':
        merge = getattr(r, 'merge_block', None)
        if merge:
            print(f"merge_block @ offset {merge.start_offset}:")
            for i in merge.instructions:
                print(f"  {i.offset:4d}  {i.opname:<30} {i.argrepr}")
            
            # Check what _generate_value_context_chain_compare_assign would do
            store_ops = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
            store_instr = None
            for instr in merge.instructions:
                if instr.opname in store_ops:
                    store_instr = instr
                    break
            print(f"\nstore_instr found: {store_instr}")
            
            if store_instr is None:
                mb_instrs = [i for i in merge.instructions if i.opname not in ('RESUME','NOP','CACHE','PUSH_NULL')]
                has_return = any(i.opname == 'RETURN_VALUE' for i in mb_instrs)
                has_swap = any(i.opname == 'SWAP' for i in mb_instrs)
                print(f"has_return: {has_return}, has_swap: {has_swap}")
