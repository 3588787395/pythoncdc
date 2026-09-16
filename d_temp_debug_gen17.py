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
cfg = build_cfg(co)

# Patch _loop_generate_for to trace exactly what happens for LoopRegion@2108
import core.cfg.region_ast_generator as rag
_orig_loop_gen_for = rag.RegionASTGenerator._loop_generate_for

class TracingGen:
    pass

def patched_loop_gen_for(self, region):
    from core.cfg.region_analyzer import LoopRegion
    h = region.header_block
    h_off = h.start_offset if h else None
    if h_off == 2108:
        fis = region.metadata.get('for_iter_setup')
        print(f'[TRACE] _loop_generate_for LoopRegion@2108')
        print(f'  fis: {fis}')
        print(f'  fis.start_offset: {fis.start_offset if fis and hasattr(fis, "start_offset") else "N/A"}')
        print(f'  fis in generated_blocks BEFORE: {fis in self.generated_blocks if fis else "N/A"}')
        
        # Check all paths in _loop_generate_for that could set iter_expr
        # Line 4138: if fis in generated_blocks -> skip to line 4138 branch
        # Line 4142: else -> extract
        if fis is not None and fis in self.generated_blocks:
            print(f'  PATH: fis in generated_blocks -> skip extraction')
        else:
            print(f'  PATH: fis NOT in generated_blocks -> extract')
        
        # Call original
        result = _orig_loop_gen_for(self, region)
        
        print(f'  fis in generated_blocks AFTER: {fis in self.generated_blocks if fis else "N/A"}')
        fis_offs = set(i.offset for i in fis.instructions) if fis else set()
        covered = fis_offs & self.generated_offsets
        print(f'  fis offsets after: {sorted(fis_offs)}')
        print(f'  covered after: {sorted(covered)}')
        print(f'  missing: {sorted(fis_offs - self.generated_offsets)}')
        
        return result
    return _orig_loop_gen_for(self, region)

rag.RegionASTGenerator._loop_generate_for = patched_loop_gen_for

gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()
