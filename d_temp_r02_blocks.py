import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

import marshal, types

with open('site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            result = find_code(const, name)
            if result:
                return result
    return None

tick = find_code(code, 'tick_worker_thread')

builder = CFGBuilder()
cfg = builder.build(tick)

# Print blocks in order
blocks = cfg.get_blocks_in_order()
print('Number of blocks: %d' % len(blocks))
for block in blocks:
    last = block.get_last_instruction()
    print('Block %d:' % block.start_offset)
    print('  preds=%s' % [p.start_offset for p in block.predecessors])
    print('  succs=%s' % [s.start_offset for s in block.successors])
    for instr in block.instructions:
        arg_str = str(instr.arg) if instr.arg is not None else ''
        argval_str = str(instr.argval) if instr.argval is not None else ''
        print('  %d: %s %s %s' % (instr.offset, instr.opname, arg_str, argval_str))
    print()
