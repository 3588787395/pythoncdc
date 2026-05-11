import sys, os
sys.path.insert(0, '.')

import py_compile
py_compile.compile('testqouter/round1/test_l04_while_break.py', 'testqouter/round1/test_l04_while_break.pyc')

from core.cfg.region_ast_generator import RegionASTGenerator
_orig_lgb = RegionASTGenerator._loop_generate_body

def _debug_lgb(self, region, *args, **kwargs):
    print("=== _loop_generate_body DEBUG ===")
    print(f"  region_type={region.region_type}")
    print(f"  header_block offset={region.header_block.start_offset if region.header_block else None}")
    print(f"  back_edge_block offset={region.back_edge_block.start_offset if region.back_edge_block else None}")
    print(f"  condition_block offset={region.condition_block.start_offset if region.condition_block else None}")
    print(f"  body_blocks offsets={[b.start_offset for b in region.body_blocks]}")
    for b in region.body_blocks:
        print(f"    Block {b.start_offset}: {[i.opname for i in b.instructions]}")
    result = _orig_lgb(self, region, *args, **kwargs)
    print(f"  result body_stmts={result}")
    print("=== END DEBUG ===")
    return result

RegionASTGenerator._loop_generate_body = _debug_lgb

from testqouter.round1.base import decompile_pyc
print("\n=== DECOMPILED ===")
print(decompile_pyc('testqouter/round1/test_l04_while_break.pyc'))
