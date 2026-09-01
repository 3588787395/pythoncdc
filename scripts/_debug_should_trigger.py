import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
import dis, marshal, types

with open('site-packages/IQEngine/utils/scheduler.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(c, name):
    if c.co_name == name: return c
    for const in c.co_consts:
        if isinstance(const, types.CodeType):
            r = find_code(const, name)
            if r: return r
    return None

c = find_code(code, '_should_trigger')
print(f'Found: {c.co_name}')

builder = CFGBuilder()
cfg = builder.build(c)
print(f'CFG blocks: {len(cfg.blocks)}')
for bid, block in cfg.blocks.items():
    instrs = [(i.opname, i.argval if hasattr(i, 'argval') else i.arg) for i in block.instructions]
    print(f'  Block {bid} (start={block.start_offset}):')
    for op, arg in instrs[:6]:
        print(f'    {op} {arg}')
    if len(instrs) > 6:
        print(f'    ... ({len(instrs)} total)')
    succ_ids = sorted([s.id for s in block.successors])
    pred_ids = sorted([p.id for p in block.predecessors])
    print(f'    succ={succ_ids}, pred={pred_ids}')

print()
ra = RegionAnalyzer(cfg)
ra.analyze()
print('Region analysis complete')
