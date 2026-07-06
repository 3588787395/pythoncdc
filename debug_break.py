import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, WithRegion, LoopRegion, IfRegion
import dis

def debug_break_in_with(src, label):
    print(f'=== {label} ===')
    code = compile(src, '<test>', 'exec')
    dis.dis(code)
    print()
    
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(code)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    
    print('Regions:')
    for r in analyzer.regions:
        rtype = type(r).__name__
        entry_off = r.entry.start_offset if r.entry else -1
        extra = ''
        if isinstance(r, WithRegion):
            body_start = getattr(r, 'body_offset_start', None)
            body_end = getattr(r, 'body_offset_end', None)
            extra = f', body=[{body_start},{body_end})'
        print(f'  {rtype}: entry={entry_off}{extra}')
        print(f'    blocks={[b.start_offset for b in r.blocks]}')
        print(f'    parent={type(r.parent).__name__ if r.parent else None}, children={[type(c).__name__ for c in r.children]}')
    
    print()
    for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
        btr = analyzer.block_to_region.get(block)
        rname = type(btr).__name__ if btr else 'None'
        has_bw = any(i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH', 'BREAK', 'CONTINUE') for i in block.instructions)
        if has_bw:
            instrs = [(i.offset, i.opname) for i in block.instructions]
            print(f'  Special block {block.start_offset}: {instrs} -> region={rname}')
    print()

# W079: for+with+break
debug_break_in_with("for i in range(3):\n    with ctx:\n        if i > 1:\n            break", "W079")

# W080: for+with+continue
debug_break_in_with("for i in range(3):\n    with ctx:\n        if i < 1:\n            continue", "W080")
