#!/usr/bin/env python3
"""R91 check which functions trigger the merge_block filter"""
import sys, marshal, types
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

def find_all_functions(code):
    result = {}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if not const.co_name.startswith('<'):
                result[const.co_name] = const
            result.update(find_all_functions(const))
    return result

all_funcs = find_all_functions(orig_code)
for func_name, func_code in sorted(all_funcs.items()):
    try:
        builder = CFGBuilder()
        cfg = builder.build(func_code)
        analyzer = RegionAnalyzer(cfg)
        regions = analyzer.analyze()
        
        for r in regions:
            if isinstance(r, IfRegion) and r.region_type.name == 'IF_ELIF_CHAIN':
                if (r.merge_block is not None
                        and getattr(r, 'elif_bodies', None)
                        and r.elif_bodies
                        and r.merge_block in r.elif_bodies[0]
                        and any(b.start_offset < r.merge_block.start_offset
                                for b in r.elif_bodies[0])):
                    print(f"  {func_name}: IfRegion@{r.entry.start_offset} merge_block={r.merge_block.start_offset} "
                          f"elif_bodies[0] has {len(r.elif_bodies[0])} blocks, "
                          f"merge at index {[i for i,b in enumerate(r.elif_bodies[0]) if b is r.merge_block]}")
    except Exception as e:
        pass
