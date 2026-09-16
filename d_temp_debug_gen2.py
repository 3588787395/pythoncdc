import sys, marshal, types
sys.stdout.reconfigure(encoding='utf-8')

# Patch _loop_generate_for to log the iter_expr
import core.cfg.region_ast_generator as rag
orig_loop_gen_for = rag.RegionASTGenerator._loop_generate_for

def patched_loop_gen_for(self, region):
    result = orig_loop_gen_for(self, region)
    h = region.header_block
    h_off = h.start_offset if hasattr(h, 'start_offset') else None
    if h_off == 2108:
        fis = region.metadata.get('for_iter_setup')
        fis_off = fis.start_offset if fis and hasattr(fis, 'start_offset') else fis
        print(f'[DEBUG] _loop_generate_for for LoopRegion@2108:')
        print(f'  for_iter_setup: {fis_off}')
        print(f'  fis in generated_blocks: {fis in self.generated_blocks if fis else None}')
        iter_expr = result.get('iter') if isinstance(result, dict) else None
        print(f'  iter_expr: {iter_expr}')
        target = result.get('target') if isinstance(result, dict) else None
        print(f'  target: {target}')
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
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()
