import sys, os
sys.path.insert(0, '.')

import core.cfg.region_ast_generator as rag

SRC_CALLS = []

# Hook _generate_ternary to log result
_orig_gt = rag.RegionASTGenerator._generate_ternary
def gt(self, region, skip_store_targets=None):
    r = _orig_gt(self, region, skip_store_targets)
    mb = getattr(region, 'merge_block', None)
    print(f"[TRACE] _generate_ternary(entry={region.condition_block.start_offset if region.condition_block else '?'}, merge={mb.start_offset if mb else '?'}) -> {type(r).__name__ if r is None else ([x.get('type') for x in r] if isinstance(r, list) else r.get('type'))}")
    if r:
        for s in (r if isinstance(r, list) else [r]):
            print(f"        stmt: {str(s)[:180]}")
    return r
rag.RegionASTGenerator._generate_ternary = gt

import pycdc
out = pycdc.decompile_pyc("site-packages/IQEngine/plugins/plugin_fly_data_source/fly_data_source.pyc")
# print only get_stock_info part
idx = out.find('def get_stock_info')
print(out[idx:idx+2500])
