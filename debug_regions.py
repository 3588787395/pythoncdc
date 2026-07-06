import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, WithRegion, TryExceptRegion, LoopRegion, IfRegion

def debug_regions(src, label):
    print(f'=== {label} ===')
    code = compile(src, '<test>', 'exec')
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(code)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    
    print(f'Regions ({len(analyzer.regions)}):')
    for r in analyzer.regions:
        rtype = type(r).__name__
        entry_off = r.entry.start_offset if r.entry else -1
        blocks_offs = sorted(b.start_offset for b in r.blocks)
        if isinstance(r, WithRegion):
            body_start = getattr(r, 'body_offset_start', None)
            body_end = getattr(r, 'body_offset_end', None)
            items = getattr(r, 'items', [])
            print(f'  {rtype}: entry={entry_off}, body=[{body_start},{body_end}), items={len(items)}, blocks={blocks_offs}')
        elif isinstance(r, TryExceptRegion):
            print(f'  {rtype}: entry={entry_off}, blocks={blocks_offs}')
            if hasattr(r, 'handler_entry_blocks'):
                for hb in r.handler_entry_blocks:
                    print(f'    handler_entry: {hb.start_offset}')
        elif isinstance(r, LoopRegion):
            print(f'  {rtype}: entry={entry_off}, blocks={blocks_offs}')
        else:
            print(f'  {rtype}: entry={entry_off}, blocks={blocks_offs}')
    
    # Check which blocks have BEFORE_WITH
    for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
        for instr in block.instructions:
            if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                btr = analyzer.block_to_region.get(block)
                print(f'  BEFORE_WITH at offset {instr.offset}, block={block.start_offset}, region={type(btr).__name__ if btr else None}')
    print()

# W05WithTry: with inside try
debug_regions("try:\n    with open('f') as a:\n        pass\nexcept IndexError:\n    pass", "W05WithTry")

# W23WithInTry: with inside try
debug_regions("try:\n    with open('f') as a:\n        pass\nexcept ValueError:\n    pass", "W23WithInTry")

# W26WithInWhile: with inside while
debug_regions("while True:\n    with open('f') as a:\n        break", "W26WithInWhile")

# W033: with+for
debug_regions("with lock:\n    for i in range(10):\n        shared += 1", "W033")

# W13WithFor: with+for
debug_regions("with open('f') as a:\n    for i in range(3):\n        pass", "W13WithFor")

# W079: for+with+break
debug_regions("for i in range(3):\n    with ctx:\n        if i > 1:\n            break", "W079")
