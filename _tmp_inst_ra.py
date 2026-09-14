import sys, os
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from pycdc import decompile_pyc
from core.cfg.region_analyzer import RegionAnalyzer
from core.pyc_loader import load_pyc

pyc_path = r'F:\Downloads\pythoncdc-main\site-packages\IQCommon\manager\instance.pyc'
code, cfg = load_pyc(pyc_path)

# Find _init_config
target = None
for const in code.co_consts:
    if hasattr(const, 'co_name') and const.co_name == '_init_config':
        target = const
        break

if target:
    from core.cfg.cfg_builder import CFGBuilder
    cfg2 = CFGBuilder(target)
    ra = RegionAnalyzer(cfg2)
    ra.analyze()
    
    # Print regions
    def print_region(r, indent=0):
        prefix = '  ' * indent
        rtype = r.region_type.name if hasattr(r, 'region_type') else type(r).__name__
        entry_off = r.entry.start_offset if r.entry else '?'
        print(f"{prefix}Region: {rtype} @ {entry_off}")
        if hasattr(r, 'then_blocks'):
            for b in r.then_blocks:
                print(f"{prefix}  then: block@{b.start_offset}")
        if hasattr(r, 'else_blocks') and r.else_blocks:
            for b in r.else_blocks:
                print(f"{prefix}  else: block@{b.start_offset}")
        if hasattr(r, 'children'):
            for c in r.children:
                print_region(c, indent + 1)
    
    for r in ra.regions:
        print_region(r)
