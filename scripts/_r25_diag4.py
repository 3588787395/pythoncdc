"""R25 diag4: Analyze BoolOpRegion prefix_block for minrepro"""
import sys, types
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, TryExceptRegion, LoopRegion

src = '''
def test():
    try:
        x = 1
    except BaseException:
        while x != 0:
            try:
                x = x - 1
            except BaseException:
                x = 0
        else:
            if x == 0:
                return None
    else:
        if x > 0:
            try:
                return x
            except BaseException:
                return None
        else:
            return -1
'''

code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test':
        target = c
        break

# Build CFG
cfg = build_cfg(target, '<test>')

# Analyze regions
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("=== Regions ===")
for r in analyzer.regions:
    rtype = type(r).__name__
    rid = getattr(r, 'region_id', '?')
    entry = getattr(r, 'entry', None)
    entry_offset = getattr(entry, 'start_offset', None) if entry else None
    prefix = getattr(r, 'prefix_block', None)
    prefix_offset = getattr(prefix, 'start_offset', None) if prefix else None
    
    if isinstance(r, BoolOpRegion):
        print(f"\nBoolOpRegion id={rid} entry_offset={entry_offset}")
        print(f"  prefix_block offset={prefix_offset}")
        if prefix:
            for i in getattr(prefix, 'instructions', []):
                print(f"    {i.offset}: {i.opname} {getattr(i, 'argval', '')}")
        print(f"  first_block offset={getattr(r, 'first_block', None) and getattr(r.first_block, 'start_offset', None)}")
        print(f"  second_block offset={getattr(r, 'second_block', None) and getattr(r.second_block, 'start_offset', None)}")
    
    if isinstance(r, TryExceptRegion):
        print(f"\nTryExceptRegion id={rid} entry_offset={entry_offset}")
        handlers = getattr(r, 'handler_entry_blocks', [])
        for h in handlers:
            h_off = getattr(h, 'start_offset', None)
            print(f"  handler_entry offset={h_off}")
            for i in getattr(h, 'instructions', []):
                print(f"    {i.offset}: {i.opname} {getattr(i, 'argval', '')}")
        else_blocks = getattr(r, 'else_blocks', [])
        print(f"  else_blocks offsets={[getattr(b, 'start_offset', None) for b in else_blocks]}")
    
    if isinstance(r, LoopRegion):
        print(f"\nLoopRegion id={rid} entry_offset={entry_offset}")
        else_blocks = getattr(r, 'else_blocks', [])
        print(f"  else_blocks offsets={[getattr(b, 'start_offset', None) for b in else_blocks]}")
