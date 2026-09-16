import sys, marshal, types, dis, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQCommon/util/replace_utils.pyc'
with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)

def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r

om = extract(orig)
code = om['decrypt_database_url']
cfg = build_cfg(code)

analyzer = RegionAnalyzer(cfg, code)
analyzer.analyze()

for region in analyzer.regions:
    rtype = region.region_type.name
    entry_off = region.entry.start_offset if region.entry else -1
    blocks_offs = sorted(b.start_offset for b in region.blocks)
    if any(b.start_offset >= 292 and b.start_offset <= 446 for b in region.blocks):
        print(f"Region: {rtype} entry={entry_off} blocks={blocks_offs}")
        if hasattr(region, 'condition_block') and region.condition_block:
            print(f"  condition_block={region.condition_block.start_offset}")
        if hasattr(region, 'true_value_block') and region.true_value_block:
            print(f"  true_value_block={region.true_value_block.start_offset}")
        if hasattr(region, 'false_value_block') and region.false_value_block:
            print(f"  false_value_block={region.false_value_block.start_offset}")
        if hasattr(region, 'then_blocks') and region.then_blocks:
            print(f"  then_blocks={sorted(b.start_offset for b in region.then_blocks)}")
        if hasattr(region, 'else_blocks') and region.else_blocks:
            print(f"  else_blocks={sorted(b.start_offset for b in region.else_blocks)}")
        if hasattr(region, 'merge_block') and region.merge_block:
            print(f"  merge_block={region.merge_block.start_offset}")
        print()
