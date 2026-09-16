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
from core.cfg.region_analyzer import LoopRegion, IfRegion, RegionType, Region
cfg = build_cfg(co)

# Find block 2094
b2094 = cfg.blocks.get(2094) or cfg.blocks.get(60)
print(f'Block 2094 object: {b2094}')
if b2094:
    print(f'  start_offset: {b2094.start_offset}')
    print(f'  instructions: {[(i.opname, i.offset) for i in b2094.instructions if i.opname not in ("RESUME", "NOP", "CACHE")]}')

# Now check which regions contain this block
gen = RegionASTGenerator(cfg, top_level_code=None)

# Patch generate to find which top-level region processes block 2094
import core.cfg.region_ast_generator as rag

_orig_gen_region = rag.RegionASTGenerator._generate_region
def patched_gen_region(self, region):
    rtype = type(region).__name__
    entry = region.entry.start_offset if region.entry else None
    has_b2094 = any(b.start_offset == 2094 for b in region.blocks) if hasattr(region, 'blocks') else False
    if has_b2094:
        print(f'_generate_region: {rtype}@{entry} CONTAINS block 2094')
        blocks_offs = sorted(b.start_offset for b in region.blocks)
        print(f'  blocks: {blocks_offs[:20]}')
    return _orig_gen_region(self, region)

rag.RegionASTGenerator._generate_region = patched_gen_region

# Also track _generate_block_statements
_orig_gen_block = rag.RegionASTGenerator._generate_block_statements
def patched_gen_block(self, block):
    if hasattr(block, 'start_offset') and block.start_offset == 2094:
        in_gen = block in self.generated_blocks
        all_offs = set(i.offset for i in block.instructions)
        covered = all_offs & self.generated_offsets
        print(f'_generate_block_statements: block@2094, in_gen={in_gen}, covered={sorted(covered)[:10]}')
    return _orig_gen_block(self, block)

rag.RegionASTGenerator._generate_block_statements = patched_gen_block

ast_dict = gen.generate()
