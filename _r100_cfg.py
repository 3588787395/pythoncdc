#!/usr/bin/env python3
"""R100: Analyze CFG blocks and region identification for check_strategy"""
import sys, marshal, types
sys.path.insert(0, '.')

pyc_path = 'site-packages/IQCommon/api/check_strategy.pyc'
code = marshal.loads(open(pyc_path, 'rb').read()[16:])
funcs = [c for c in code.co_consts if isinstance(c, types.CodeType)]
cs = [f for f in funcs if f.co_name == 'check_strategy'][0]

# Build CFG
from core.cfg.cfg_builder import CFGBuilder
builder = CFGBuilder()
cfg = builder.build(cs)

print('=== Blocks in check_strategy ===')
for block in cfg.get_blocks_in_order():
    last = block.get_last_instruction()
    print(f'  Block @ {block.start_offset:4d} (end ~{last.offset if last else "?":>4}): ', end='')
    instrs_summary = []
    for instr in block.instructions:
        instrs_summary.append(f'{instr.opname}({instr.arg})' if instr.arg is not None else instr.opname)
    print(', '.join(instrs_summary[:8]) + ('...' if len(instrs_summary) > 8 else ''))

print('\n=== Successors ===')
for block in cfg.get_blocks_in_order():
    succs = [s.start_offset for s in block.successors]
    conds = [s.start_offset for s in block.conditional_successors]
    print(f'  Block @ {block.start_offset:4d}: successors={succs}, conditional={conds}')
