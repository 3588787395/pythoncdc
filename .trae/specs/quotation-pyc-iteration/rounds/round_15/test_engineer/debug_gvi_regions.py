"""Debug region structure for get_valuation_info"""
import sys
import types
import marshal
sys.path.insert(0, '/workspace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, RegionType

PYC = '/workspace/quotation.pyc'

with open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

result = {}
def _collect(c, result, prefix):
    name = prefix + '.' + c.co_name if prefix else '<module>'
    result[name] = c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            _collect(k, result, name)

_collect(code, result, '')

target_code = result['<module>.get_valuation_info']
print(f"=== get_valuation_info ===")
print(f"co_consts: {target_code.co_consts}")
print(f"co_names: {target_code.co_names}")
print(f"co_varnames: {target_code.co_varnames}")

cfg = build_cfg(target_code)
ra = RegionAnalyzer(cfg)
ra.analyze()

print(f"\n=== Regions ({len(ra.regions)}) ===")
for r in ra.regions:
    print(f"\n--- Region id={id(r)} type={type(r).__name__} region_type={getattr(r, 'region_type', 'N/A')} ---")
    print(f"  entry: {r.entry.start_offset if r.entry else None}")
    if hasattr(r, 'condition_block') and r.condition_block:
        print(f"  condition_block: {r.condition_block.start_offset}")
    if hasattr(r, 'then_blocks') and r.then_blocks:
        print(f"  then_blocks: {[b.start_offset for b in r.then_blocks]}")
    if hasattr(r, 'else_blocks') and r.else_blocks:
        print(f"  else_blocks: {[b.start_offset for b in r.else_blocks]}")
    if hasattr(r, 'elif_conditions') and r.elif_conditions:
        print(f"  elif_conditions: {[b.start_offset for b in r.elif_conditions]}")
    if hasattr(r, 'elif_bodies') and r.elif_bodies:
        for i, eb in enumerate(r.elif_bodies):
            print(f"  elif_bodies[{i}]: {[b.start_offset for b in eb]}")
    if hasattr(r, 'elif_final_else') and r.elif_final_else:
        print(f"  elif_final_else: {[b.start_offset for b in r.elif_final_else]}")
    if hasattr(r, 'blocks') and r.blocks:
        print(f"  blocks: {[b.start_offset for b in r.blocks]}")
    if hasattr(r, 'children') and r.children:
        print(f"  children: {[(type(c).__name__, c.entry.start_offset if hasattr(c, 'entry') and c.entry else None) for c in r.children]}")
    if hasattr(r, 'merge_block') and r.merge_block:
        print(f"  merge_block: {r.merge_block.start_offset}")

print(f"\n=== All blocks ===")
for b in cfg.blocks:
    instrs = [(i.offset, i.opname, i.argval) for i in b.instructions]
    succs = [s.start_offset for s in b.successors]
    print(f"  Block {b.start_offset}: succs={succs}")
    for ins in instrs:
        print(f"    {ins}")
