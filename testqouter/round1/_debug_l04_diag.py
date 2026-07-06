import sys, os
sys.path.insert(0, '.')

import py_compile
py_compile.compile('testqouter/round1/test_l04_while_break.py', 'testqouter/round1/test_l04_while_break.pyc')

from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import LoopRegion, IfRegion, BlockRole

_orig_lgb = RegionASTGenerator._loop_generate_body
_orig_gen_for = RegionASTGenerator._loop_generate_for
_orig_gen_while = RegionASTGenerator._loop_generate_while

def _debug_lgb(self, region, *args, **kwargs):
    print("=" * 70)
    print("_loop_generate_body ENTER")
    print("=" * 70)
    print(f"  region_type={region.region_type}")
    hb = region.header_block
    print(f"  header_block offset={hb.start_offset if hb else None}")
    print(f"  back_edge_block offset={region.back_edge_block.start_offset if region.back_edge_block else None}")
    print(f"  condition_block offset={region.condition_block.start_offset if region.condition_block else None}")
    print(f"  body_blocks offsets={[b.start_offset for b in region.body_blocks]}")
    print(f"  else_blocks offsets={[b.start_offset for b in region.else_blocks]}")
    print(f"  has_break={region.has_break}")

    print(f"\n  Body blocks content:")
    for b in region.body_blocks:
        role = self.block_role(b)
        print(f"    Block {b.start_offset}: role={role}")
        print(f"      succs={[s.start_offset for s in b.successors]}")
        print(f"      instrs: {[i.opname for i in b.instructions]}")

    print(f"\n  Children regions:")
    for child in (region.children or []):
        ctype = type(child).__name__
        if isinstance(child, LoopRegion):
            print(f"    {ctype}: type={child.region_type}, header={child.header_block.start_offset if child.header_block else None}, blocks={[b.start_offset for b in child.blocks]}")
        elif isinstance(child, IfRegion):
            print(f"    {ctype}: cond={child.condition_block.start_offset if child.condition_block else None}, then={[b.start_offset for b in child.then_blocks]}, else={[b.start_offset for b in child.else_blocks]}")
        else:
            print(f"    {ctype}: blocks={[b.start_offset for b in child.blocks]}")

    result = _orig_lgb(self, region, *args, **kwargs)
    print(f"\n  RESULT body_stmts count={len(result)}")
    for i, s in enumerate(result):
        print(f"    [{i}] type={s.get('type', '?')}: keys={list(s.keys())}")
        if s.get('type') == 'If':
            print(f"         test={s.get('test')}")
            print(f"         body={s.get('body')}")
    print("=" * 70)
    return result

def _debug_while(self, region, **kwargs):
    print("\n>>> _loop_generate_while called")
    print(f"    region_type={region.region_type}")
    print(f"    condition_block offset={region.condition_block.start_offset if region.condition_block else None}")
    print(f"    header_block offset={region.header_block.start_offset if region.header_block else None}")
    print(f"    is_while_true={region.is_while_true}")
    result = _orig_gen_while(self, region, **kwargs)
    print(f"<<< _loop_generate_while result type={result.get('type') if isinstance(result, dict) else 'list'}")
    return result

RegionASTGenerator._loop_generate_body = _debug_lgb
RegionASTGenerator._loop_generate_while = _debug_while

from testqouter.round1.base import decompile_pyc
print("\n" + "=" * 70)
print("FINAL DECOMPILED OUTPUT")
print("=" * 70)
print(decompile_pyc('testqouter/round1/test_l04_while_break.pyc'))
