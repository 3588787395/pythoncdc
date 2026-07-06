import sys, dis
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
from core.cfg.code_generator import CodeGenerator

source = 'try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1'
code = compile(source, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

print("ALL BLOCKS:")
for block in cfg.get_blocks_in_order():
    role = RegionAnalyzer(cfg).get_block_role(block)
    print(f"  Block @ {block.start_offset}: {[(i.opname, i.argval) for i in block.instructions]}")
    print(f"    role: {role.name}, succs: {[b.start_offset for b in block.successors]}")
