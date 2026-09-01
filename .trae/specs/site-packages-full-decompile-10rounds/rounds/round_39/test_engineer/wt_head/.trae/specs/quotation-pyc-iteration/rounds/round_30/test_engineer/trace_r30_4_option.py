"""R30-4 trace: which region generates the if-not in get_option_info"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

module = load_pyc_file_v2('/workspace/quotation.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find_co(co, name):
    if co.co_name == name: return co
    for c in co.co_consts:
        if isinstance(c, type(co)):
            r = find_co(c, name)
            if r: return r
    return None

co = find_co(code_obj, 'get_option_info')
cfg = CFGBuilder().build(co)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

gen = RegionASTGenerator(cfg, analyzer)

# Find both IfRegions
targets = {}
for r in analyzer.regions:
    if r.entry and r.entry.start_offset in (602, 622) and type(r).__name__ == 'IfRegion':
        targets[r.entry.start_offset] = r
        print(f"IfRegion@{r.entry.start_offset}: type={r.region_type.name} then={[b.start_offset for b in r.then_blocks]} else={[b.start_offset for b in r.else_blocks] if r.else_blocks else None}")

# Patch _generate_if to trace ALL IfRegions in the 600-740 range
orig_gi = gen._generate_if
def traced_gi(region):
    e = region.entry.start_offset if region.entry else None
    if e is not None and 590 <= e <= 740:
        print(f"\n[_generate_if] IfRegion@{e} type={region.region_type.name}")
    result = orig_gi(region)
    if e is not None and 590 <= e <= 740:
        if isinstance(result, list):
            print(f"  -> list: {[s.get('type') if isinstance(s, dict) else type(s).__name__ for s in result]}")
        elif isinstance(result, dict):
            t = result.get('type')
            print(f"  -> {t}")
            if t == 'If':
                print(f"     test={result.get('test')}")
                bt = [bs.get('type') if isinstance(bs, dict) else type(bs).__name__ for bs in result.get('body', [])]
                ot = [bs.get('type') if isinstance(bs, dict) else type(bs).__name__ for bs in result.get('orelse', [])] if result.get('orelse') else None
                print(f"     body={bt} orelse={ot}")
    return result
gen._generate_if = traced_gi

# Patch _generate_region
orig_gr = gen._generate_region
call_depth = [0]
def traced_gr(region):
    e = region.entry.start_offset if region.entry else None
    is_target = e is not None and 590 <= e <= 740 and type(region).__name__ == 'IfRegion'
    if is_target:
        print(f"\n[_generate_region] {type(region).__name__}@{e}")
    result = orig_gr(region)
    return result
gen._generate_region = traced_gr

# Patch _if_generate_full_elif_chain
orig_elif = gen._if_generate_full_elif_chain
def traced_elif(region):
    e = region.entry.start_offset if region.entry else None
    if e is not None and 590 <= e <= 740:
        print(f"\n[_if_generate_full_elif_chain] IfRegion@{e}")
    return orig_elif(region)
gen._if_generate_full_elif_chain = traced_elif

# Patch _if_generate_then_branch
orig_then = gen._if_generate_then_branch
def traced_then(region):
    result = orig_then(region)
    e = region.entry.start_offset if region.entry else None
    if e is not None and 590 <= e <= 740:
        print(f"  [then_branch] IfRegion@{e} -> {[s.get('type') if isinstance(s, dict) else type(s).__name__ for s in result]}")
    return result
gen._if_generate_then_branch = traced_then

ast = gen.generate()
