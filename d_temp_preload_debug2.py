import sys
sys.path.insert(0, '.')
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.cfg_builder import CFGBuilder
import marshal, types

with open('site-packages/IQCommon/util/replace_utils.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func_code = code.co_consts[21]

builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

for r in regions:
    if hasattr(r, 'container_type'):
        if hasattr(r, 'entry') and hasattr(r.entry, 'offset'):
            entry_off = r.entry.offset
        else:
            entry_off = r.entry
        if entry_off != 292:
            continue
        
        offset = getattr(r, '_ternary_cond_start_offset', None)
        print('_ternary_cond_start_offset=%s' % offset)

print('Done')
