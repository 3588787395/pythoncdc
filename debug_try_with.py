import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, WithRegion, TryExceptRegion
import dis

def debug_try_with(src, label):
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
        if isinstance(r, WithRegion):
            body_start = getattr(r, 'body_offset_start', None)
            body_end = getattr(r, 'body_offset_end', None)
            print(f'  {rtype}: entry={entry_off}, body=[{body_start},{body_end}), parent={type(r.parent).__name__ if r.parent else None}')
        elif isinstance(r, TryExceptRegion):
            print(f'  {rtype}: entry={entry_off}, parent={type(r.parent).__name__ if r.parent else None}')
            print(f'    try_blocks={[b.start_offset for b in r.try_blocks]}')
            print(f'    children={[type(c).__name__ for c in r.children]}')
    
    print()
    for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
        btr = analyzer.block_to_region.get(block)
        rname = type(btr).__name__ if btr else 'None'
        has_bw = any(i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for i in block.instructions)
        if has_bw:
            print(f'  BEFORE_WITH block {block.start_offset} -> region={rname}')
    print()

# with containing try/except
debug_try_with('with ctx:\n    try:\n        pass\n    except:\n        pass', "with > try/except")

# try containing with
debug_try_with("try:\n    with open('f') as a:\n        pass\nexcept IndexError:\n    pass", "try > with")
