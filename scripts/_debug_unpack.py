import sys, marshal, types
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

pyc_path = 'site-packages/IQData/plugins/plugin_system_realquote/real_quote.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(c, name):
    if c.co_name == name: return c
    for const in c.co_consts:
        if isinstance(const, types.CodeType):
            r = find_code(const, name)
            if r: return r
    return None

co = find_code(code, 'get_underlying_code')

builder = CFGBuilder()
cfg = builder.build(co)
ra = RegionAnalyzer(cfg)
ra.analyze()

# Find BoolOpRegion with entry=10
for r in ra.regions:
    if type(r).__name__ == 'BoolOpRegion' and r.entry and r.entry.id == 10:
        print(f"BoolOpRegion entry=10:")
        print(f"  blocks: {sorted([b.id for b in r.blocks])}")
        print(f"  merge_block: {r.merge_block.id if r.merge_block else None}")
        print(f"  op_chain: {getattr(r, 'op_chain', None)}")
        for b in sorted(r.blocks, key=lambda b: b.start_offset):
            print(f"\n  Block {b.id} (start_offset={b.start_offset}):")
            for i in b.instructions:
                if i.opname not in ('RESUME', 'NOP', 'CACHE'):
                    print(f"    offset={getattr(i,'offset','?')}: {i.opname} {getattr(i, 'argval', '')}")
            print(f"    successors: {[s.id for s in b.successors]}")
        
        # Also print merge_block
        if r.merge_block:
            print(f"\n  Merge block {r.merge_block.id} (start_offset={r.merge_block.start_offset}):")
            for i in r.merge_block.instructions:
                if i.opname not in ('RESUME', 'NOP', 'CACHE'):
                    print(f"    offset={getattr(i,'offset','?')}: {i.opname} {getattr(i, 'argval', '')}")
