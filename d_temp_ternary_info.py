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
    if isinstance(region, type(None).__class__):
        continue
    rtype = region.region_type.name
    if rtype == 'TERNARY' and region.entry and region.entry.start_offset == 292:
        print(f"TERNARY entry=292:")
        print(f"  merge_context = {getattr(region, 'merge_context', 'NOT SET')}")
        print(f"  value_target = {getattr(region, 'value_target', 'NOT SET')}")
        print(f"  container_type = {getattr(region, 'container_type', 'NOT SET')}")
        print(f"  func_call_info = {getattr(region, 'func_call_info', 'NOT SET')}")
        print(f"  condition_block = {region.condition_block.start_offset if region.condition_block else None}")
        print(f"  true_value_block = {region.true_value_block.start_offset if region.true_value_block else None}")
        print(f"  false_value_block = {region.false_value_block.start_offset if region.false_value_block else None}")
        print(f"  merge_block = {region.merge_block.start_offset if region.merge_block else None}")
