"""Diagnostic: trace _generate_try on backtest.pyc to find why the handler at
offset 2438 (try_range 2394-2436) is dropped.

Monkey-patches RegionASTGenerator._generate_try to log, for each TryExceptRegion:
  - try_range, handler_entry_blocks, except_handlers count
  - _pre_consumed_handler_entries (which handler entries were already generated)
  - for each handler: whether handler_entry is in generated_blocks at loop time
    (-> skipped) and the spurious-ternary check result.
"""
import sys, os, marshal, types
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _ in range(8):
    if os.path.exists(os.path.join(sys.path[0], 'pycdc.py')):
        break
    sys.path[0] = os.path.dirname(sys.path[0])

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import TryExceptRegion, RegionAnalyzer

_orig = RegionASTGenerator._generate_try

def traced(self, region):
    if isinstance(region, TryExceptRegion):
        tr = (region.try_offset_start, region.try_offset_end)
        if tr == (2394, 2436):
            hebs = [b.start_offset for b in region.handler_entry_blocks]
            print('\n=== _generate_try ENTER try_range=%s ===' % (tr,))
            print('  handler_entry_blocks=', hebs)
            print('  except_handlers=', [(et, en, [b.start_offset for b in hb])
                                         for et, en, hb in region.except_handlers])
            _heb_set = set(region.handler_entry_blocks)
            _pre = _heb_set & self.generated_blocks
            print('  _pre_consumed_handler_entries=', [b.start_offset for b in _pre])
            # Check what region owns the handler entry 2438 in block_to_region
            for heb in region.handler_entry_blocks:
                owner = self.region_analyzer.block_to_region.get(heb)
                print('  handler_entry %d owner_region=%s' % (
                    heb.start_offset, type(owner).__name__ if owner else None))
    return _orig(self, region)

RegionASTGenerator._generate_try = traced

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
try:
    ast_dict = gen.generate()
    print('\n[generate completed OK]')
except Exception as e:
    import traceback
    traceback.print_exc()
