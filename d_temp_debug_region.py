import sys, logging
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

# Enable debug logging for region_analyzer
logging.basicConfig(level=logging.WARNING)

from core.cfg.cfg_builder import ControlFlowGraph
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.basic_block import BasicBlock

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_persist/__init__.pyc'
import marshal
with open(pyc, 'rb') as f:
    f.read(16); code = marshal.load(f)

import types
def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r

for name, co in extract(code).items():
    if name == 'setup':
        print('=== Analyzing setup ===')
        cfg = ControlFlowGraph(co)
        analyzer = RegionAnalyzer(cfg)
        regions = analyzer.analyze()
        
        for r in regions:
            if hasattr(r, 'try_blocks'):
                print('\nTryExceptRegion:')
                print('  entry=%s' % (r.entry.start_offset if r.entry else None))
                print('  try_offset_start=%s try_offset_end=%s' % (r.try_offset_start, r.try_offset_end))
                print('  try_blocks=%s' % [b.start_offset for b in r.try_blocks])
                print('  has_else=%s' % getattr(r, 'has_else', False))
                print('  else_blocks=%s' % [b.start_offset for b in getattr(r, 'else_blocks', [])])
                print('  except_handlers:')
                for ht, hn, hb in getattr(r, 'except_handlers', []):
                    print('    type=%s name=%s blocks=%s' % (ht, hn, [b.start_offset for b in hb]))
                print('  handler_entry_blocks=%s' % [b.start_offset for b in getattr(r, 'handler_entry_blocks', [])])
                if hasattr(r, 'finally_blocks'):
                    print('  finally_blocks=%s' % [b.start_offset for b in r.finally_blocks])
