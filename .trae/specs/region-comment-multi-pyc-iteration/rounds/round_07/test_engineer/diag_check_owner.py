"""Check block_to_region owner of 2438 + TryExceptRegion details for backtest."""
import sys, os, marshal, types
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _ in range(8):
    if os.path.exists(os.path.join(sys.path[0], 'pycdc.py')):
        break
    sys.path[0] = os.path.dirname(sys.path[0])

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import TryExceptRegion, WithRegion

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
gen = RegionASTGenerator(cfg)
# force analyze
gen.generate()

b2r = gen.region_analyzer.block_to_region
# find block 2438
blk2438 = None
for b in cfg.blocks.values():
    if b.start_offset == 2438:
        blk2438 = b
        break
print('block 2438 found:', blk2438 is not None)
if blk2438 is not None:
    owner = b2r.get(blk2438)
    print('block_to_region[2438] =', type(owner).__name__ if owner is not None else None)

print('\n=== TryExceptRegions ===')
for _r in gen.regions:
    if isinstance(_r, TryExceptRegion):
        print('  TryExceptRegion entry=%s' % (_r.entry.start_offset if _r.entry else None))
        print('    try_blocks=', sorted(b.start_offset for b in _r.try_blocks))
        print('    handler_entry_blocks=', sorted(b.start_offset for b in _r.handler_entry_blocks))
        print('    handler_body_blocks=', sorted(b.start_offset for b in getattr(_r, 'handler_body_blocks', [])))
        print('    blocks=', sorted(b.start_offset for b in _r.blocks))
        # is 2438 in this region's handler_entry_blocks?
        if blk2438 is not None:
            print('    2438 in handler_entry_blocks?', blk2438 in _r.handler_entry_blocks)
            print('    2438 in blocks?', blk2438 in _r.blocks)

print('\n=== WithRegions (cleanup/exception) ===')
for _r in gen.regions:
    if isinstance(_r, WithRegion):
        cb = sorted(b.start_offset for b in getattr(_r, 'cleanup_blocks', []))
        eb = sorted(b.start_offset for b in getattr(_r, 'exception_blocks', []))
        print('  WithRegion entry=%s cleanup=%s exception=%s' % (_r.entry.start_offset if _r.entry else None, cb, eb))
        if blk2438 is not None:
            print('    2438 in cleanup?', blk2438 in getattr(_r, 'cleanup_blocks', []))
            print('    2438 in exception?', blk2438 in getattr(_r, 'exception_blocks', []))
            print('    2438 in blocks?', blk2438 in _r.blocks)
