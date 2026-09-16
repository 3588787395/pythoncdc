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
        print('type(entry)=%s entry=%s' % (type(entry).__name__, entry))
        if hasattr(entry, 'offset'):
            print('  entry.offset=%s' % entry.offset)
