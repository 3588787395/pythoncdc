import sys, marshal, types
sys.stdout.reconfigure(encoding='utf-8')

# Patch to track generated_offsets changes for block 2094
import core.cfg.region_ast_generator as rag
orig_add = rag.RegionASTGenerator.__init__

def patched_init(self, *args, **kwargs):
    result = orig_add(self, *args, **kwargs)
    self._debug_2094_offsets = set()
    return result

rag.RegionASTGenerator.__init__ = patched_init

# Patch generated_offsets.add to track
orig_gen_for = rag.RegionASTGenerator._loop_generate_for

def patched_gen_for(self, region):
    from core.cfg.region_analyzer import LoopRegion
    h = region.header_block
    h_off = h.start_offset if hasattr(h, 'start_offset') else None
    if h_off == 2108:
        fis = region.metadata.get('for_iter_setup')
        if fis:
            # Before _loop_generate_for
            offsets_before = set(self.generated_offsets)
            result = orig_gen_for(self, region)
            offsets_after = set(self.generated_offsets)
            new_offsets = offsets_after - offsets_before
            print(f'[DEBUG] After _loop_generate_for for LoopRegion@2108:')
            print(f'  New offsets: {sorted(new_offsets)[:20]}')
            # Check if all of block 2094's instruction offsets are covered
            b2094 = self.cfg.get_block_by_offset(2094)
            b2094_offsets = set(i.offset for i in b2094.instructions)
            covered = b2094_offsets & self.generated_offsets
            uncovered = b2094_offsets - self.generated_offsets
            print(f'  Block 2094 offsets: {sorted(b2094_offsets)}')
            print(f'  Covered: {sorted(covered)}')
            print(f'  Uncovered: {sorted(uncovered)}')
            return result
    return orig_gen_for(self, region)

rag.RegionASTGenerator._loop_generate_for = patched_gen_for

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
