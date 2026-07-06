import os, sys, dis

_self_dir = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(_self_dir))
sys.path.insert(0, PROJ)

from core.cfg.cfg_builder import build_cfg, ControlFlowGraph

TEST_DIR = _self_dir
py_path = os.path.join(TEST_DIR, 'test_w04_nested_with.py')
with open(py_path, 'r') as f:
    orig_source = f.read()
code = compile(orig_source, '<test>', 'exec')

test_func = None
for const in code.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'test':
        test_func = const
        break

print('Using build_cfg...')
cfg = build_cfg(test_func, 'test')
print(f'cfg type: {type(cfg).__name__}')
print(f'cfg.blocks count: {len(cfg.blocks)}')
print(f'exception_table count: {len(cfg.exception_table)}')

for entry in cfg.exception_table:
    print(f'  start={entry["start"]:#x} end={entry["end"]:#x} target={entry["target"]:#x} depth={entry["depth"]}')

print(f'\nBlocks:')
for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    has_bw = any(i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for i in block.instructions)
    marker = ' *** BW ***' if has_bw else ''
    print(f'Block id={block.id} start={block.start_offset:#x} ({block.start_offset}){marker}')
    for instr in block.instructions:
        line_str = f'L{instr.starts_line}' if instr.starts_line else '   '
        print(f'  {instr.offset:#x} {line_str} {instr.opname:<28s} {str(instr.argval):<15s}')
    print(f'  successors: {[hex(s.start_offset) for s in block.successors]}')
    print(f'  exc_succs: {[hex(s.start_offset) for s in block.exception_successors]}')
    print()
