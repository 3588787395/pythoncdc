import sys, marshal, types, dis
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
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion
cfg = build_cfg(co)
ra = RegionAnalyzer(cfg)
ra.analyze()

# Find lr1818 and its parent chain
lr1818 = None
lr2108 = None
for region in ra.regions:
    if isinstance(region, LoopRegion):
        h = region.header_block
        h_off = h.start_offset if hasattr(h, 'start_offset') else None
        if h_off == 1818:
            lr1818 = region
        elif h_off == 2108:
            lr2108 = region

# Parent chain of lr1818
p = lr1818.parent
while p:
    ptype = type(p).__name__
    pblocks = [b.start_offset for b in p.blocks] if hasattr(p, 'blocks') else []
    pchildren = [(type(c).__name__,) for c in (p.children or [])]
    pentry = p.entry.start_offset if hasattr(p, 'entry') and hasattr(p.entry, 'start_offset') else None
    pmerge = p.merge_block.start_offset if hasattr(p, 'merge_block') and p.merge_block and hasattr(p.merge_block, 'start_offset') else None
    print(f'{ptype}: entry={pentry} merge={pmerge} blocks={pblocks[:10]}...')
    p = p.parent if hasattr(p, 'parent') else None

# Check if lr2108 is in any of the parent's children
print()
print(f'lr2108 parent: {type(lr2108.parent).__name__ if lr2108.parent else None}')
print(f'lr2108 in same region tree as lr1818: {lr2108.parent is not None}')

# What does the top-level region structure look like?
print()
print('Top-level regions (no parent):')
for region in ra.regions:
    if region.parent is None:
        rtype = type(region).__name__
        if hasattr(region, 'header_block') and hasattr(region.header_block, 'start_offset'):
            print(f'  {rtype} header={region.header_block.start_offset}')
        elif hasattr(region, 'entry') and hasattr(region.entry, 'start_offset'):
            print(f'  {rtype} entry={region.entry.start_offset}')
        else:
            print(f'  {rtype}')
        if hasattr(region, 'merge_block') and region.merge_block and hasattr(region.merge_block, 'start_offset'):
            print(f'    merge_block={region.merge_block.start_offset}')
