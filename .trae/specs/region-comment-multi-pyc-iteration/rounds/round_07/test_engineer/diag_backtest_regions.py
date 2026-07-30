"""Diagnostic: run RegionAnalyzer directly on backtest.pyc handle_backtest_build
and dump all TryExceptRegions, especially the one at try_offset_start ~2394
(the shutil.copy try whose except handler is dropped).
"""
import sys, os, marshal, types
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _ in range(8):
    if os.path.exists(os.path.join(sys.path[0], 'pycdc.py')):
        break
    sys.path[0] = os.path.dirname(sys.path[0])

from core.cfg import build_cfg, RegionASTGenerator
from core.cfg.region_analyzer import TryExceptRegion, RegionAnalyzer

PYC = r"F:\Downloads\pythoncdc-main\site-packages\IQCommon\backtest\backtest.pyc"
with open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find(co, name):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                return c
            r = find(c, name)
            if r:
                return r
    return None

fn = find(code, 'handle_backtest_build')
cfg = build_cfg(fn, 'handle_backtest_build')
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print(f'#regions = {len(regions)}')
for r in regions:
    if isinstance(r, TryExceptRegion):
        print('\n[TryExceptRegion] try_range=({},{})'.format(r.try_offset_start, r.try_offset_end))
        print('  entry=', r.entry.start_offset if r.entry else None)
        print('  try_blocks=', sorted(b.start_offset for b in r.try_blocks))
        print('  handler_entry_blocks=', [b.start_offset for b in r.handler_entry_blocks])
        print('  except_handlers (%d):' % len(r.except_handlers))
        for i, (et, en, hb) in enumerate(r.except_handlers):
            print('    [%d] exc=%r as=%r blocks=%s' % (i, et, en, sorted(b.start_offset for b in hb)))
        print('  else_blocks=', sorted(b.start_offset for b in r.else_blocks))
        print('  finally_blocks=', sorted(b.start_offset for b in r.finally_blocks))
        print('  cleanup_blocks=', sorted(b.start_offset for b in r.cleanup_blocks))
        print('  has_else=%s has_finally=%s' % (r.has_else, r.has_finally))

# Also dump block_to_region for the handler entry region around 2438
print('\n--- block_to_region around the broken try (2380-2510) ---')
for off in sorted(b.start_offset for b in cfg.blocks.values() if 2380 <= b.start_offset <= 2510):
    blk = cfg.get_block_by_offset(off)
    r = analyzer.block_to_region.get(blk) if hasattr(analyzer, 'block_to_region') else None
    rname = type(r).__name__ if r is not None else 'None'
    instrs = ','.join(i.opname for i in blk.instructions[:4])
    print('  off=%d role=%s region=%s instrs=%s' % (off, analyzer.get_block_role(blk) if hasattr(analyzer,'get_block_role') else '?', rname, instrs))
