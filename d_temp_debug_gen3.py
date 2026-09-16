import sys, marshal, types
sys.stdout.reconfigure(encoding='utf-8')

# Patch _generate_region and _loop_generate_for to track order
import core.cfg.region_ast_generator as rag
orig_gen_region = rag.RegionASTGenerator._generate_region
orig_loop_gen_for = rag.RegionASTGenerator._loop_generate_for
call_order = []

def patched_gen_region(self, region):
    from core.cfg.region_analyzer import LoopRegion, IfRegion
    rtype = type(region).__name__
    if isinstance(region, LoopRegion):
        h = region.header_block
        h_off = h.start_offset if hasattr(h, 'start_offset') else None
        call_order.append(f'generate_region LoopRegion@{h_off}')
    elif isinstance(region, IfRegion):
        entry = region.entry
        e_off = entry.start_offset if hasattr(entry, 'start_offset') else None
        call_order.append(f'generate_region IfRegion@{e_off}')
    return orig_gen_region(self, region)

def patched_loop_gen_for(self, region):
    h = region.header_block
    h_off = h.start_offset if hasattr(h, 'start_offset') else None
    call_order.append(f'loop_generate_for LoopRegion@{h_off}')
    return orig_loop_gen_for(self, region)

rag.RegionASTGenerator._generate_region = patched_gen_region
rag.RegionASTGenerator._loop_generate_for = patched_loop_gen_for

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
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()

print('Call order:')
for i, call in enumerate(call_order):
    print(f'  {i+1}. {call}')
