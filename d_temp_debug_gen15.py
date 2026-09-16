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
from core.cfg.region_analyzer import LoopRegion, IfRegion, RegionType
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)

# Access regions through the generator
ra = gen.region_analyzer
print(f'Type of ra: {type(ra)}')
print(f'Has regions attr: {hasattr(ra, "regions")}')
if hasattr(ra, 'regions'):
    print(f'Total regions: {len(ra.regions)}')
else:
    # Try other ways
    print(dir(ra))

# Also check if there's a different way to get regions
# Maybe they're built during generate()
import core.cfg.region_ast_generator as rag
orig_generate = rag.RegionASTGenerator.generate

def patched_generate(self, *args, **kwargs):
    result = orig_generate(self, *args, **kwargs)
    # After generate, regions should be populated
    if hasattr(self, 'regions'):
        print(f'After generate: {len(self.regions)} regions')
        for r in sorted(self.regions, key=lambda r: r.entry.start_offset if r and r.entry else 0):
            rtype = type(r).__name__
            entry_off = r.entry.start_offset if r and r.entry else None
            if rtype in ('LoopRegion', 'IfRegion'):
                extra = ''
                if isinstance(r, LoopRegion):
                    fis = r.metadata.get('for_iter_setup')
                    fis_off = fis.start_offset if fis and hasattr(fis, 'start_offset') else fis
                    extra = f' fis={fis_off}'
                print(f'  {rtype}@{entry_off}{extra}')
    return result

rag.RegionASTGenerator.generate = patched_generate
gen2 = RegionASTGenerator(cfg, top_level_code=None)
gen2.generate()
