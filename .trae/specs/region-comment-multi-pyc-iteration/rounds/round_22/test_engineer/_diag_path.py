"""R22: check which path _find_loop_else takes for api_base"""
import marshal, sys, types, json
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

# Temporarily patch _find_loop_else
import core.cfg.region_analyzer as ra_mod
_orig = ra_mod.RegionAnalyzer._find_loop_else

def _patched(self, header, loop_body, loop_type, for_iter_exit=None, condition_block=None):
    body_set = loop_body | {header}
    print(f'\n[_find_loop_else] loop_type={loop_type} header={header.start_offset}')
    print(f'  body={[b.start_offset for b in sorted(loop_body, key=lambda x: x.start_offset)]}')
    print(f'  for_iter_exit={for_iter_exit.start_offset if for_iter_exit else None}')
    print(f'  condition_block={condition_block.start_offset if condition_block else None}')
    
    result = _orig(self, header, loop_body, loop_type, for_iter_exit, condition_block)
    print(f'  RESULT: else_blocks={[b.start_offset for b in result[0]] if result[0] else None} natural_exit={result[1].start_offset if result[1] else None}')
    return result

ra_mod.RegionAnalyzer._find_loop_else = _patched

from pycdc import decompile_pyc
with open(r'f:/Downloads/pythoncdc-main/pyc_index.json', 'r') as f:
    index = json.load(f)

pyc_path = None
for e in index:
    if 'api_base.pyc' in e.get('path', ''):
        pyc_path = e['path']
        break

try:
    dec_src = decompile_pyc(pyc_path)
    print('\nDecompile OK')
except Exception as ex:
    print(f'\nDecompile error: {ex}')
