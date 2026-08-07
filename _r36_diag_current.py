#!/usr/bin/env python3
"""Debug: check current state of is_stock_trade_trigger regions after all fixes."""

import sys, os, marshal, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, RegionType
from core.cfg.region_ast_generator import RegionASTGenerator, SHORT_CIRCUIT_JUMP_OPS, FORWARD_CONDITIONAL_JUMP_OPS

PYC_PATH = os.path.join(HERE, 'site-packages', 'IQEngine', 'utils', 'trade_schedule.pyc')

with open(PYC_PATH, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            sub = find_code(const, name)
            if sub:
                return sub
    return None

stt = find_code(code, 'is_stock_trade_trigger')

builder = CFGBuilder()
cfg = builder.build(stt)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("=== All Regions (from analyzer) ===")
for r in analyzer.regions:
    rtype = type(r).__name__
    entry_off = r.entry.start_offset if r.entry else None
    blocks = [b.start_offset for b in r.blocks]
    print(f"  {rtype}: entry={entry_off}, blocks={blocks}")
    if isinstance(r, IfRegion):
        print(f"    condition_block={r.condition_block.start_offset if r.condition_block else None}")
        print(f"    then_blocks={[b.start_offset for b in r.then_blocks]}")
        print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")
        print(f"    merge_block={r.merge_block.start_offset if r.merge_block else None}")
        print(f"    elif_conditions={[b.start_offset for b in r.elif_conditions]}")
        print(f"    elif_bodies={[[b.start_offset for b in body] for body in r.elif_bodies]}")
        print(f"    elif_final_else={[b.start_offset for b in r.elif_final_else]}")
        print(f"    region_type={r.region_type}")
        cc_ops = getattr(r, 'chained_compare_ops', None)
        if cc_ops:
            print(f"    chained_compare_ops={cc_ops}")
            print(f"    chained_compare_blocks={[b.start_offset for b in getattr(r, 'chained_compare_blocks', [])]}")
            print(f"    chained_left_instr={getattr(r, 'chained_left_instr', None)}")
            print(f"    chained_comparator_instrs={getattr(r, 'chained_comparator_instrs', None)}")
    if isinstance(r, BoolOpRegion):
        print(f"    op_chain={[(b.start_offset, op) for b, op in r.op_chain]}")
        print(f"    merge_block={r.merge_block.start_offset if r.merge_block else None}")

print("\n=== Block to Region mapping ===")
for block in cfg.get_blocks_in_order():
    br = analyzer.block_to_region.get(block)
    if br:
        print(f"  block@{block.start_offset} -> {type(br).__name__}(entry={br.entry.start_offset if br.entry else None})")

print("\n=== CFG Blocks ===")
for block in cfg.get_blocks_in_order():
    last = block.get_last_instruction()
    succs = [s.start_offset for s in block.successors]
    print(f"  block@{block.start_offset}: last={last.opname}({last.argval}), succs={succs}")

# Now test with RegionASTGenerator
print("\n=== RegionASTGenerator test ===")
ast_gen = RegionASTGenerator(cfg)
result = ast_gen.generate()
print(f"  result type: {type(result)}")

# Print decompiled code
from core.cfg.code_generator import CodeGenerator
cg = CodeGenerator()
code_str = cg.generate(ast_gen.ast if hasattr(ast_gen, 'ast') else result)
print(f"\n=== Decompiled ===")
print(code_str)
