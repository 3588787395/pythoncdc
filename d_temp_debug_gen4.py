import sys, marshal, types
sys.stdout.reconfigure(encoding='utf-8')

# Patch _loop_generate_for to debug
import core.cfg.region_ast_generator as rag
orig_loop_gen_for = rag.RegionASTGenerator._loop_generate_for

def patched_loop_gen_for(self, region):
    from core.cfg.region_analyzer import LoopRegion
    h = region.header_block
    h_off = h.start_offset if hasattr(h, 'start_offset') else None
    if h_off == 2108:
        fis = region.metadata.get('for_iter_setup')
        fis_off = fis.start_offset if fis and hasattr(fis, 'start_offset') else fis
        fis_in_gen = fis in self.generated_blocks if fis else None
        fis_in_offsets = fis.start_offset in self.generated_offsets if fis and hasattr(fis, 'start_offset') else None
        print(f'[DEBUG] _loop_generate_for LoopRegion@2108:')
        print(f'  for_iter_setup: {fis_off}')
        print(f'  fis in generated_blocks: {fis_in_gen}')
        print(f'  fis.start_offset in generated_offsets: {fis_in_offsets}')
        if fis:
            instrs = [i for i in fis.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            print(f'  fis instructions: {[(i.opname, i.arg) for i in instrs]}')
            _fis_pre, _fis_iter = self._loop_extract_for_iter_pre_stmts(instrs, fis)
            print(f'  fis_pre: {_fis_pre}')
            print(f'  fis_iter: {[(i.opname, i.arg) for i in _fis_iter]}')
            iter_expr = self.expr_reconstructor.reconstruct(_fis_iter) if _fis_iter else None
            print(f'  iter_expr from reconstruct: {iter_expr}')
        # Check what _entry_prefix_emitted_blocks contains
        print(f'  fis in _entry_prefix_emitted_blocks: {fis in self._entry_prefix_emitted_blocks}')
    
    result = orig_loop_gen_for(self, region)
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
