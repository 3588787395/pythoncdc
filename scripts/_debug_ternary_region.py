import sys, os, types
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TernaryRegion, IfRegion

pyc_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'site-packages', 'IQEngine', 'plugins', 'plugin_system_risk_calculation', '__init__.pyc'))

module = load_pyc_file_v2(pyc_path)
code_obj = module.code
if hasattr(code_obj, 'get'):
    code_obj = code_obj.get()
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find_func(code_obj, name):
    if hasattr(code_obj, 'co_name') and code_obj.co_name == name:
        return code_obj
    if hasattr(code_obj, 'co_consts'):
        for c in code_obj.co_consts:
            if isinstance(c, types.CodeType):
                result = find_func(c, name)
                if result:
                    return result
    return None

target_func = find_func(code_obj, 'get_daily_summary')
cfg = build_cfg(target_func)
analyzer = RegionAnalyzer(cfg, target_func)
regions = analyzer.analyze()

print(f"Total regions: {len(regions)}")
for i, r in enumerate(regions):
    blocks = sorted([b.start_offset for b in r.blocks]) if hasattr(r, 'blocks') and r.blocks else []
    if any(3660 <= b <= 4100 for b in blocks):
        rtype = type(r).__name__
        entry = r.entry.start_offset if r.entry else None
        print(f"\n{rtype}[{i}]: entry={entry} blocks={blocks}")
        if isinstance(r, IfRegion):
            then_blocks = sorted([b.start_offset for b in r.then_blocks]) if hasattr(r, 'then_blocks') and r.then_blocks else []
            else_blocks = sorted([b.start_offset for b in r.else_blocks]) if hasattr(r, 'else_blocks') and r.else_blocks else []
            merge = r.merge_block.start_offset if r.merge_block else None
            print(f"  then={then_blocks} else={else_blocks} merge={merge}")
