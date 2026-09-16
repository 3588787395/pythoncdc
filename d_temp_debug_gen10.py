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

# Patch to track block@68 (offset 2274)
orig_loop_gen_for = RegionASTGenerator._loop_generate_for
def patched_loop_gen_for(self, region):
    from core.cfg.region_analyzer import LoopRegion
    h = region.header_block
    h_off = h.start_offset if h else None
    fis = region.metadata.get('for_iter_setup')
    fis_off = fis.start_offset if fis and hasattr(fis, 'start_offset') else fis
    if fis_off in (2094, 2274):
        print(f'_loop_generate_for: LoopRegion@{h_off}, fis={fis_off}')
        fis_in_gen = fis in self.generated_blocks if fis else None
        print(f'  fis in generated_blocks: {fis_in_gen}')
        if fis:
            all_offsets = set(i.offset for i in fis.instructions)
            covered = all_offsets & self.generated_offsets
            uncovered = all_offsets - self.generated_offsets
            print(f'  fis offsets: {sorted(all_offsets)}')
            print(f'  covered: {sorted(covered)}')
            print(f'  uncovered: {sorted(uncovered)}')
    return orig_loop_gen_for(self, region)

RegionASTGenerator._loop_generate_for = patched_loop_gen_for

# Also patch _generate_block_statements_body for block 2274
orig_gen_body = RegionASTGenerator._generate_block_statements_body
def patched_gen_body(self, block, _cjb_parent=None):
    b_off = block.start_offset if hasattr(block, 'start_offset') else None
    if b_off == 2274:
        in_gen = block in self.generated_blocks
        all_offsets = set(i.offset for i in block.instructions)
        covered = all_offsets & self.generated_offsets
        print(f'_generate_block_statements_body: block@{b_off}')
        print(f'  in generated_blocks: {in_gen}')
        print(f'  offsets: {sorted(all_offsets)}')
        print(f'  covered offsets: {sorted(covered)}')
    return orig_gen_body(self, block, _cjb_parent)

RegionASTGenerator._generate_block_statements_body = patched_gen_body

ast_dict = gen.generate()
