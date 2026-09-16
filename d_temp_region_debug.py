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
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion
cfg = build_cfg(co)
ra = RegionAnalyzer(cfg)
ra.analyze()

# Find the LoopRegion for field loop at 1818 and stock loop at 2108
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

if lr1818:
    print("LoopRegion 1818 (field loop):")
    print("  blocks:", [b.start_offset for b in lr1818.blocks])
    fis = lr1818.metadata.get('for_iter_setup')
    print("  for_iter_setup:", fis.start_offset if fis and hasattr(fis, 'start_offset') else fis)
    print("  entry:", lr1818.entry.start_offset if hasattr(lr1818.entry, 'start_offset') else lr1818.entry)

if lr2108:
    print("\nLoopRegion 2108 (stock loop):")
    print("  blocks:", [b.start_offset for b in lr2108.blocks])
    fis = lr2108.metadata.get('for_iter_setup')
    print("  for_iter_setup:", fis.start_offset if fis and hasattr(fis, 'start_offset') else fis)
    print("  entry:", lr2108.entry.start_offset if hasattr(lr2108.entry, 'start_offset') else lr2108.entry)

# Check: is block 2094's LOAD_FAST+GET_ITER consumed by lr1818 generation?
# When lr1818 generates, it processes block 2094 as its last block
# Block 2094 contains: LOAD_FAST sql_code, LOAD_CONST, BINARY_OP+=, STORE_FAST sql_code, 
#                       LOAD_FAST security, GET_ITER
# The first 4 instructions are for sql_code += (common code)
# The last 2 are the setup for the stock loop
# When lr1818 generates, it should output the sql_code += part
# but NOT the LOAD_FAST security + GET_ITER part

# The question is: does the code know to split block 2094?
print("\nBlock 2094 instructions:")
b2094 = cfg.get_block_by_offset(2094)
for inst in b2094.instructions:
    print(f"  {inst.offset} {inst.opname} {inst.arg} {getattr(inst, 'argrepr', '')}")
