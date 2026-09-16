import sys, marshal, types
sys.stdout.reconfigure(encoding='utf-8')

# Patch _loop_generate_for to debug the result
import core.cfg.region_ast_generator as rag
orig_loop_gen_for = rag.RegionASTGenerator._loop_generate_for

def patched_loop_gen_for(self, region):
    from core.cfg.region_analyzer import LoopRegion
    result = orig_loop_gen_for(self, region)
    h = region.header_block
    h_off = h.start_offset if hasattr(h, 'start_offset') else None
    if h_off == 2108:
        print(f'[DEBUG] _loop_generate_for LoopRegion@2108 result:')
        if isinstance(result, list):
            for i, item in enumerate(result):
                itype = item.get('type') if isinstance(item, dict) else type(item).__name__
                extra = ''
                if itype == 'For':
                    iter_node = item.get('iter')
                    target = item.get('target')
                    extra = f' iter={iter_node} target={target}'
                print(f'  result[{i}]: type={itype}{extra}')
        elif isinstance(result, dict):
            itype = result.get('type')
            iter_node = result.get('iter')
            target = result.get('target')
            print(f'  result: type={itype} iter={iter_node} target={target}')
    return result

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
