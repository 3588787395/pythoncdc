"""R30 测试工程师：dump get_date_and_count region structure"""
import sys
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator, IfRegion, LoopRegion, BoolOpRegion, TernaryRegion, RegionType

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# Find get_date_and_count
def find_func(co, name):
    for c in co.co_consts:
        if isinstance(c, type(co)) and c.co_name == name:
            return c
        if isinstance(c, type(co)):
            r = find_func(c, name)
            if r: return r
    return None

target = find_func(code_obj, 'get_date_and_count')
cfg = build_cfg(target)
gen = RegionASTGenerator(cfg, top_level_code=None)

# Don't generate, just analyze regions
# Access the region analyzer
ra = gen._region_analyzer if hasattr(gen, '_region_analyzer') else None

# Try to get regions
try:
    regions = gen.regions if hasattr(gen, 'regions') else []
    if not regions:
        # Need to run analysis first
        gen.generate()
        regions = gen.regions
except:
    gen.generate()
    regions = gen.regions

print(f"=== get_date_and_count regions ({len(regions)}) ===")
for r in sorted(regions, key=lambda r: r.entry.start_offset if r.entry else 0):
    rtype = type(r).__name__
    entry = r.entry.start_offset if r.entry else None
    blocks = sorted([b.start_offset for b in r.blocks]) if hasattr(r, 'blocks') else []
    if isinstance(r, IfRegion):
        rtype_str = r.region_type.name if hasattr(r, 'region_type') else 'IF?'
        then_b = [b.start_offset for b in r.then_blocks] if hasattr(r, 'then_blocks') and r.then_blocks else []
        else_b = [b.start_offset for b in r.else_blocks] if hasattr(r, 'else_blocks') and r.else_blocks else []
        merge = r.merge_block.start_offset if r.merge_block else None
        elif_conds = [b.start_offset for b in r.elif_conditions] if hasattr(r, 'elif_conditions') and r.elif_conditions else []
        elif_bodies = [[b.start_offset for b in body] if body else [] for body in r.elif_bodies] if hasattr(r, 'elif_bodies') and r.elif_bodies else []
        print(f"  {rtype}({rtype_str})@{entry}: blocks={blocks}")
        print(f"    then={then_b} else={else_b} merge={merge}")
        if elif_conds:
            print(f"    elif_conds={elif_conds} elif_bodies={elif_bodies}")
    elif isinstance(r, LoopRegion):
        body_b = [b.start_offset for b in r.body_blocks] if hasattr(r, 'body_blocks') and r.body_blocks else []
        else_b = [b.start_offset for b in r.else_blocks] if hasattr(r, 'else_blocks') and r.else_blocks else []
        print(f"  {rtype}@{entry}: blocks={blocks}")
        print(f"    body={body_b} else={else_b}")
    else:
        print(f"  {rtype}@{entry}: blocks={blocks}")
