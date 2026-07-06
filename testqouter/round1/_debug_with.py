import sys, os
os.chdir(r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1')
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, WithRegion, TryExceptRegion

tf = 'test_w03_multi_with.py'
with open(tf) as f:
    source = f.read()
code = compile(source, tf, 'exec')
func_code = code.co_consts[0]

builder = CFGBuilder()
cfg = builder.build(func_code)
print(f'=== {tf} ===')
for offset, block in sorted(cfg.blocks.items()):
    instrs = [f'{i.opname}({getattr(i, "argval", "")})' for i in block.instructions]
    succs = [s.start_offset for s in block.successors]
    exc_succs = [s.start_offset for s in block.exception_successors]
    print(f'  Block {offset}: instrs={instrs}')
    print(f'    succs={succs}, exc_succs={exc_succs}')

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
print(f'\nTotal regions: {len(regions)}')
for r in regions:
    rtype = type(r).__name__
    print(f'  {rtype}: entry={r.entry.start_offset}, blocks=sorted({sorted(b.start_offset for b in r.blocks)})')
    if isinstance(r, WithRegion):
        print(f'    with_blocks={[b.start_offset for b in r.with_blocks]}')
        print(f'    target={r.target}')
        print(f'    items={[(len(instrs), tgt) for instrs, tgt in r.items]}')
        print(f'    body_offset_start={r.body_offset_start}')
        print(f'    body_offset_end={r.body_offset_end}')
        print(f'    Entry block instructions:')
        for instr in r.entry.instructions:
            print(f'      {instr.offset}: {instr.opname} {getattr(instr, "argval", "")}')
