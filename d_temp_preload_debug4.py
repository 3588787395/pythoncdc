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
        entry = r.entry
        if not hasattr(entry, 'offset'):
            continue
        if entry.offset != 292:
            continue
        
        offset = getattr(r, '_ternary_cond_start_offset', None)
        print('_ternary_cond_start_offset=%s' % offset)
        mc = getattr(r, 'merge_context', None)
        fci = getattr(r, 'func_call_info', None)
        print('merge_context=%s func_call_info=%s' % (mc, fci))
