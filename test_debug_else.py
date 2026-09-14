import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

# Monkey-patch _find_loop_else to add debug output
_orig_find_loop_else = RegionAnalyzer._find_loop_else

def _debug_find_loop_else(self, header, loop_body, loop_type, for_iter_exit=None, condition_block=None):
    print(f'\n_find_loop_else called: header={header.start_offset}, loop_type={loop_type}')
    print(f'  condition_block={condition_block.start_offset if condition_block else None}')
    print(f'  loop_body={[b.start_offset for b in loop_body]}')
    result = _orig_find_loop_else(self, header, loop_body, loop_type, for_iter_exit, condition_block)
    print(f'  result: else_blocks={[b.start_offset for b in result[0]] if result[0] else None}, natural_exit={result[1].start_offset if result[1] else None}')
    return result

RegionAnalyzer._find_loop_else = _debug_find_loop_else

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
