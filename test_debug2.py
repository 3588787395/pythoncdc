import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

# Monkey-patch _find_loop_else and LoopRegion creation
_orig_find_loop_else = RegionAnalyzer._find_loop_else
_orig_loop_init = LoopRegion.__init__

def _debug_find_loop_else(self, header, loop_body, loop_type, for_iter_exit=None, condition_block=None):
    result = _orig_find_loop_else(self, header, loop_body, loop_type, for_iter_exit, condition_block)
    print(f'_find_loop_else: header={header.start_offset}, cond={condition_block.start_offset if condition_block else None}, '
          f'else_blocks={[b.start_offset for b in result[0]] if result[0] else None}')
    return result

RegionAnalyzer._find_loop_else = _debug_find_loop_else

# Monkey-patch the region creation line
import types
_orig_analyze = RegionAnalyzer._identify_loop_regions

def _debug_analyze(self):
    result = _orig_analyze(self)
    for r in result:
        if isinstance(r, LoopRegion):
            print(f'Created LoopRegion: header={r.header_block.start_offset}, '
                  f'else_blocks={[b.start_offset for b in r.else_blocks] if r.else_blocks else None}')
    return result

RegionAnalyzer._identify_loop_regions = _debug_analyze

src = '''
def test_while_else_nested_break(data):
    while data:
        item = data[0]
        if item < 0:
            data.pop(0)
            continue
        if item == 0:
            break
        data.pop(0)
    else:
        data.append(-1)
    return data
'''

code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_code'):
        cfg = build_cfg(c)
        ra = RegionAnalyzer(cfg)
        regions = ra.analyze()
