import sys, marshal, types
sys.stdout.reconfigure(encoding='utf-8')
pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQData/plugins/plugin_system_local_finance/finance_data_source.pyc'
with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)
def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r
om = extract(orig)
co = om['growth_factors_sql_get']
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import LoopRegion, IfRegion
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)

# Force region analysis
gen.generate()

# Find LoopRegion@2108
for r in gen.regions:
    if isinstance(r, LoopRegion) and r.header_block and r.header_block.start_offset == 2108:
        parent = r.parent
        ptype = type(parent).__name__ if parent else None
        p_off = parent.header_block.start_offset if parent and hasattr(parent, 'header_block') else None
        print(f'LoopRegion@2108 parent: {ptype}@{p_off}')
        # Check all ancestors
        ancestor = parent
        while ancestor:
            atype = type(ancestor).__name__
            a_off = ancestor.header_block.start_offset if hasattr(ancestor, 'header_block') else None
            a_parent = ancestor.parent
            ap_type = type(a_parent).__name__ if a_parent else None
            ap_off = a_parent.header_block.start_offset if a_parent and hasattr(a_parent, 'header_block') else None
            print(f'  ancestor: {atype}@{a_off}, parent: {ap_type}@{ap_off}')
            ancestor = a_parent
