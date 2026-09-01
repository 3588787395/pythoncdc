"""R23-N10: 调试load_get_exrights的merge_block生成问题"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, TryExceptRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# Find load_get_exrights
def find(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_consts'):
            r = find(c, name)
            if r: return r
    return None

co = find(code_obj, 'load_get_exrights')
print(f"Found: {co.co_name}")

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(co)

analyzer = RegionAnalyzer(cfg, co)
analyzer.analyze()

# Find the if-isinstance-str IfRegion
print("\n=== All IfRegions ===")
for r in analyzer.regions:
    if isinstance(r, IfRegion):
        entry_off = r.entry.start_offset if r.entry else None
        merge_off = r.merge_block.start_offset if r.merge_block else None
        then_offs = [b.start_offset for b in r.then_blocks] if r.then_blocks else []
        else_offs = [b.start_offset for b in r.else_blocks] if r.else_blocks else []
        print(f"  IfRegion entry={entry_off} merge={merge_off}")
        print(f"    then={then_offs}")
        print(f"    else={else_offs}")
        if hasattr(r, 'elif_conditions') and r.elif_conditions:
            print(f"    elif_conds={[b.start_offset for b in r.elif_conditions]}")
            print(f"    elif_bodies={[[b.start_offset for b in body] for body in r.elif_bodies]}")
            print(f"    elif_final_else={[b.start_offset for b in r.elif_final_else] if r.elif_final_else else []}")

# Find the block at offset 1078 (return data)
print("\n=== Block at offset 1078 ===")
for b in cfg.blocks:
    b_off = b.start_offset if hasattr(b, 'start_offset') else b
    if b_off == 1078:
        print(f"  Block@{b_off}: {[i.opname for i in b.instructions]}")
        print(f"  predecessors: {[p.start_offset for p in b.predecessors]}")
        print(f"  successors: {[s.start_offset for s in b.successors]}")
        break

# Check which region owns block 1078
print("\n=== Region ownership of block 1078 ===")
for r in analyzer.regions:
    if hasattr(r, 'blocks') and any(b.start_offset == 1078 for b in r.blocks):
        print(f"  {type(r).__name__} entry={r.entry.start_offset if r.entry else None} owns block 1078")
        if hasattr(r, 'merge_block') and r.merge_block:
            print(f"    merge_block={r.merge_block.start_offset}")
        if hasattr(r, 'else_blocks'):
            print(f"    else_blocks={[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")
        if hasattr(r, 'body_blocks'):
            print(f"    body_blocks={[b.start_offset for b in r.body_blocks] if r.body_blocks else []}")
        if hasattr(r, 'header_block') and r.header_block:
            print(f"    header_block={r.header_block.start_offset}")
        print(f"    blocks={[b.start_offset for b in r.blocks]}")

# Also check the IfRegion entry=830's merge_block handling
print("\n=== IfRegion entry=830 details ===")
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 830:
        print(f"  merge_block={r.merge_block.start_offset if r.merge_block else None}")
        print(f"  then_blocks={[b.start_offset for b in r.then_blocks]}")
        print(f"  else_blocks={[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")
        # Check if merge_block is in then/else
        if r.merge_block:
            in_then = r.merge_block in r.then_blocks
            in_else = r.else_blocks and r.merge_block in r.else_blocks
            print(f"  merge_block in then_blocks: {in_then}")
            print(f"  merge_block in else_blocks: {in_else}")
        break
