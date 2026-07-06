import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, WithRegion, LoopRegion, BlockRole

def debug_block_roles(src, label):
    print(f'=== {label} ===')
    code = compile(src, '<test>', 'exec')
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(code)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    
    for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
        role = analyzer.get_block_role(block)
        if role != BlockRole.NORMAL:
            instrs = [(i.offset, i.opname) for i in block.instructions]
            print(f'  Block {block.start_offset}: role={role.name}, instrs={instrs}')
    print()

# W079: for+with+break
debug_block_roles("for i in range(3):\n    with ctx:\n        if i > 1:\n            break", "W079")

# W080: for+with+continue
debug_block_roles("for i in range(3):\n    with ctx:\n        if i < 1:\n            continue", "W080")
