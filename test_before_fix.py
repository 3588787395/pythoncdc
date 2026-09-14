import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

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
        
        # Monkey-patch _find_loop_else
        _orig = RegionAnalyzer._find_loop_else
        def _debug(self, header, loop_body, loop_type, for_iter_exit=None, condition_block=None):
            result = _orig(self, header, loop_body, loop_type, for_iter_exit, condition_block)
            print(f'_find_loop_else: header={header.start_offset}, cond={condition_block.start_offset if condition_block else None}, '
                  f'else_blocks={[b.start_offset for b in result[0]] if result[0] else None}, natural_exit={result[1].start_offset if result[1] else None}')
            return result
        RegionAnalyzer._find_loop_else = _debug
        
        regions = ra.analyze()
        for r in ra.regions:
            if isinstance(r, LoopRegion):
                print(f'Final: header={r.header_block.start_offset}, else_blocks={[b.start_offset for b in r.else_blocks] if r.else_blocks else None}')
