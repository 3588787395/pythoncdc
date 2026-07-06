import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, WithRegion, TryExceptRegion, LoopRegion
import dis

def debug_blocks(src, label):
    print(f'=== {label} ===')
    code = compile(src, '<test>', 'exec')
    print('Bytecode:')
    dis.dis(code)
    print()
    
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(code)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    
    print('Blocks:')
    for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
        instrs = [(i.offset, i.opname, i.argval) for i in block.instructions]
        btr = analyzer.block_to_region.get(block)
        rname = type(btr).__name__ if btr else 'None'
        print(f'  Block {block.start_offset}: {instrs} -> region={rname}')
    
    print()
    print('Regions:')
    for r in analyzer.regions:
        rtype = type(r).__name__
        entry_off = r.entry.start_offset if r.entry else -1
        if isinstance(r, WithRegion):
            body_start = getattr(r, 'body_offset_start', None)
            body_end = getattr(r, 'body_offset_end', None)
            items = getattr(r, 'items', [])
            print(f'  {rtype}: entry={entry_off}, body=[{body_start},{body_end}), items={len(items)}')
            print(f'    parent={type(r.parent).__name__ if r.parent else None}, children={[type(c).__name__ for c in r.children]}')
        elif isinstance(r, TryExceptRegion):
            print(f'  {rtype}: entry={entry_off}')
            print(f'    parent={type(r.parent).__name__ if r.parent else None}, children={[type(c).__name__ for c in r.children]}')
            print(f'    try_blocks={[b.start_offset for b in r.try_blocks]}')
        elif isinstance(r, LoopRegion):
            print(f'  {rtype}: entry={entry_off}')
            print(f'    parent={type(r.parent).__name__ if r.parent else None}, children={[type(c).__name__ for c in r.children]}')
    print()

# W05WithTry: with inside try
debug_blocks("try:\n    with open('f') as a:\n        pass\nexcept IndexError:\n    pass", "W05WithTry")

# W26WithInWhile: with inside while
debug_blocks("while True:\n    with open('f') as a:\n        break", "W26WithInWhile")
