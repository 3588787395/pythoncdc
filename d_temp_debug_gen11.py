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
gen = RegionASTGenerator(cfg, top_level_code=None)

# Patch _loop_generate_for for LoopRegion@2440
orig_loop_gen_for = RegionASTGenerator._loop_generate_for
def patched_loop_gen_for(self, region):
    from core.cfg.region_analyzer import LoopRegion
    h = region.header_block
    h_off = h.start_offset if h else None
    fis = region.metadata.get('for_iter_setup')
    fis_off = fis.start_offset if fis and hasattr(fis, 'start_offset') else fis
    if h_off == 2440:
        print(f'_loop_generate_for: LoopRegion@{h_off}, fis={fis_off}')
        # Check _fis_is_self_setup
        _fis_is_self_setup = (fis in region.blocks or fis is region.metadata.get('for_iter_setup'))
        print(f'  fis_is_self_setup: {_fis_is_self_setup}')
        print(f'  fis in region.blocks: {fis in region.blocks}')
        print(f'  fis is for_iter_setup: {fis is region.metadata.get("for_iter_setup")}')
        fis_in_gen = fis in self.generated_blocks if fis else None
        print(f'  fis in generated_blocks: {fis_in_gen}')
        if fis:
            instrs = [i for i in fis.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            _fis_pre_stmts, _fis_iter_instrs = self._loop_extract_for_iter_pre_stmts(instrs, fis)
            print(f'  fis_pre count: {len(_fis_pre_stmts)}')
            print(f'  fis_iter: {[(i.opname, i.offset) for i in _fis_iter_instrs]}')
            iter_expr = self.expr_reconstructor.reconstruct(_fis_iter_instrs) if _fis_iter_instrs else None
            print(f'  iter_expr: {iter_expr}')
            # Now check what _fis_pre_stmts contains
            for idx, ps in enumerate(_fis_pre_stmts):
                print(f'  pre[{idx}]: type={ps.get("type") if isinstance(ps, dict) else type(ps).__name__}')
        # Run original
        result = orig_loop_gen_for(self, region)
        if isinstance(result, list):
            for i, item in enumerate(result):
                itype = item.get('type') if isinstance(item, dict) else type(item).__name__
                extra = ''
                if itype == 'For':
                    extra = ' iter=%s target=%s' % (item.get('iter'), item.get('target'))
                print(f'  result[{i}]: type={itype}{extra}')
        elif isinstance(result, dict):
            itype = result.get('type')
            extra = ''
            if itype == 'For':
                extra = ' iter=%s target=%s' % (result.get('iter'), result.get('target'))
            print(f'  result: type={itype}{extra}')
        return result
    return orig_loop_gen_for(self, region)

RegionASTGenerator._loop_generate_for = patched_loop_gen_for

ast_dict = gen.generate()
