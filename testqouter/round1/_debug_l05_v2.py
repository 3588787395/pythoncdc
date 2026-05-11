import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import py_compile

test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_l05_while_continue.py')
pyc_file = test_file + 'c'
py_compile.compile(test_file, pyc_file, doraise=True)

from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import LoopRegion

_orig_lgb = RegionASTGenerator._loop_generate_body

def debug_lgb(self, region, *args, **kwargs):
    print("=== _loop_generate_body ===")
    print(f"  header offset={region.header_block.start_offset if region.header_block else None}")
    print(f"  back_edge_block offset={region.back_edge_block.start_offset if region.back_edge_block else None}")
    print(f"  condition_block offset={region.condition_block.start_offset if region.condition_block else None}")
    print(f"  body_blocks={[b.start_offset for b in region.body_blocks]}")
    
    natural_back_edge = region.back_edge_block
    print(f"  natural_back_edge offset={natural_back_edge.start_offset if natural_back_edge else None}")
    
    for block in region.body_blocks:
        role = self.block_role(block)
        is_nbe = block == natural_back_edge
        last_instr = block.get_last_instruction()
        last_op = last_instr.opname if last_instr else None
        ops = [i.opname for i in block.instructions]
        print(f"  Block {block.start_offset}: role={role.name}, is_back_edge={is_nbe}, last_op={last_op}, ops={ops}")
    
    result = _orig_lgb(self, region, *args, **kwargs)
    print(f"  result body_stmts={result}")
    print("=== END ===")
    return result

RegionASTGenerator._loop_generate_body = debug_lgb

from base import decompile_pyc

print("\n=== DECOMPILED ===")
print(decompile_pyc(pyc_file))

os.remove(pyc_file)
