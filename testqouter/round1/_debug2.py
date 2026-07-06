import sys, os
os.chdir(r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1')
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, BoolOpRegion, TernaryRegion, IfRegion

tf = 'test_r1_if_while_break.py'
with open(tf) as f:
    source = f.read()
code = compile(source, tf, 'exec')
func_code = code.co_consts[0]

builder = CFGBuilder()
cfg = builder.build(func_code)
print(f'=== {tf} ===')
for offset, block in sorted(cfg.blocks.items()):
    instrs = [f'{i.opname}({i.argval})' for i in block.instructions]
    succs = [s.start_offset for s in block.successors]
    print(f'  Block {offset}: instrs={instrs}, succs={succs}')

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
print(f'\nTotal regions: {len(regions)}')
for r in regions:
    rtype = type(r).__name__
    print(f'  {rtype}: entry={r.entry.start_offset}, blocks=sorted({sorted(b.start_offset for b in r.blocks)})')
    if isinstance(r, LoopRegion):
        print(f'    header={r.header_block.start_offset if r.header_block else None}, cond={r.condition_block.start_offset if r.condition_block else None}')
        print(f'    body={[b.start_offset for b in r.body_blocks]}')
        print(f'    else_blocks={[b.start_offset for b in r.else_blocks]}')
        print(f'    init={[b.start_offset for b in r.init_blocks]}')
    elif isinstance(r, BoolOpRegion):
        print(f'    op_chain={[(b.start_offset, op) for b, op in r.op_chain]}')
    elif isinstance(r, IfRegion):
        print(f'    cond={r.condition_block.start_offset}, then={[b.start_offset for b in r.then_blocks]}, else={[b.start_offset for b in r.else_blocks] if r.else_blocks else []}')
        print(f'    merge={r.merge_block.start_offset if r.merge_block else None}')
