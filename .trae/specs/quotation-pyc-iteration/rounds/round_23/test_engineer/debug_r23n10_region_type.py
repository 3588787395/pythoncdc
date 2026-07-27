"""R23-N10: 检查load_get_exrights的IfRegion entry=830的region_type"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

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

# Find ALL IfRegions and show their region_type
print("\n=== All IfRegions with region_type ===")
for r in analyzer.regions:
    if isinstance(r, IfRegion):
        entry_off = r.entry.start_offset if r.entry else None
        merge_off = r.merge_block.start_offset if r.merge_block else None
        rt = getattr(r, 'region_type', None)
        rt_name = rt.name if rt is not None else 'None'
        print(f"  IfRegion entry={entry_off} merge={merge_off} region_type={rt_name}")
        if entry_off == 830:
            print(f"    *** TARGET region_type={rt_name}")
            print(f"    then={[b.start_offset for b in r.then_blocks] if r.then_blocks else []}")
            print(f"    else={[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")
            print(f"    elif_conditions={[b.start_offset for b in r.elif_conditions] if r.elif_conditions else []}")
            print(f"    elif_bodies={[[b.start_offset for b in body] for body in r.elif_bodies] if r.elif_bodies else []}")
            print(f"    elif_final_else={[b.start_offset for b in r.elif_final_else] if r.elif_final_else else []}")
            print(f"    children={[c.entry.start_offset if c.entry else None for c in (r.children or [])]}")

# Check the IfRegion that owns block 992 (elif body)
print("\n=== Region ownership of block 992 (elif body) ===")
for r in analyzer.regions:
    if hasattr(r, 'blocks') and any(b.start_offset == 992 for b in r.blocks):
        entry_off = r.entry.start_offset if r.entry else None
        rt = getattr(r, 'region_type', None)
        rt_name = rt.name if rt is not None else 'None'
        print(f"  {type(r).__name__} entry={entry_off} region_type={rt_name} owns block 992")
        if isinstance(r, LoopRegion):
            print(f"    else_blocks={[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")
            print(f"    blocks={[b.start_offset for b in r.blocks]}")

# Check the function entry that calls _generate_if
print("\n=== Calling _generate_if for IfRegion entry=830 ===")
target = None
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 830:
        target = r
        break

if target:
    # Check what _generate_if would do
    rt = target.region_type
    print(f"  region_type.name: {rt.name}")
    print(f"  Is IF_ELIF_CHAIN: {rt.name == 'IF_ELIF_CHAIN'}")
