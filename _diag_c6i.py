import sys
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator

source = 'try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1'
code = compile(source, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

# Check get_block_by_offset
for offset in [40, 42, 44, 50]:
    block = cfg.get_block_by_offset(offset)
    print(f"get_block_by_offset({offset}): {block.start_offset if block else None}")

# Check the last instruction of block 28
block28 = cfg.get_block_by_offset(28)
last = block28.get_last_instruction()
print(f"\nBlock 28 last instr: offset={last.offset}, opname={last.opname}, argval={last.argval}")
print(f"last.offset + 2 = {last.offset + 2}")
ft_block = cfg.get_block_by_offset(last.offset + 2)
print(f"get_block_by_offset({last.offset + 2}): {ft_block.start_offset if ft_block else None}")
