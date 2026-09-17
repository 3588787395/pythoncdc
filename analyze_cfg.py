import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc'
with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)

def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r

om = extract(orig)
match_co = om['match']

cfg = build_cfg(match_co)
blocks = cfg.get_blocks_in_order()
print(f"Number of basic blocks: {len(blocks)}")
print(f"Entry block: {cfg.entry_block.start_offset if cfg.entry_block else 'None'}")

for block in blocks:
    succ_offsets = [s.start_offset for s in block.successors]
    instrs = list(block.instructions)
    last_instr = instrs[-1] if instrs else None
    last_op = last_instr.opname if last_instr else 'N/A'
    first_off = block.start_offset
    end_off = block.end_offset if hasattr(block, 'end_offset') else first_off
    print(f"  Block {first_off:5d}-{end_off:5d} succ={succ_offsets} last={last_op}")

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
print(f"\nTotal regions: {len(regions)}")

for r in regions:
    if isinstance(r, IfRegion):
        entry_off = r.entry.start_offset if r.entry else -1
        cond_off = r.condition_block.start_offset if r.condition_block else -1
        merge_off = r.merge_block.start_offset if r.merge_block else -1
        then_offs = [b.start_offset for b in r.then_blocks] if r.then_blocks else []
        else_offs = [b.start_offset for b in r.else_blocks] if r.else_blocks else []
        elif_conds = [b.start_offset for b in r.elif_conditions] if r.elif_conditions else []
        elif_bodies = [[b.start_offset for b in body] for body in r.elif_bodies] if r.elif_bodies else []
        elif_final_else = [b.start_offset for b in r.elif_final_else] if r.elif_final_else else []
        print(f"\n  IfRegion: entry={entry_off} cond={cond_off} merge={merge_off}")
        print(f"    then={then_offs}")
        print(f"    else={else_offs}")
        print(f"    elif_conds={elif_conds}")
        print(f"    elif_bodies={elif_bodies}")
        print(f"    elif_final_else={elif_final_else}")
    elif isinstance(r, LoopRegion):
        entry_off = r.entry.start_offset if r.entry else -1
        print(f"\n  LoopRegion: entry={entry_off}")
