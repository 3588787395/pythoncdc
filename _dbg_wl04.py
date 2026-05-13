import sys, types
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

source = 'while a > 0:\n    a -= 1\n    if a == 5:\n        continue'
code = compile(source, '<test>', 'exec')
print('code.co_consts:', [(type(c).__name__, getattr(c, 'co_name', None)) for c in code.co_consts])
func = code
print('func type:', type(func).__name__)

from core.cfg.cfg_builder import CFGBuilder
cfg = CFGBuilder().build(func)
for b in cfg.blocks.values():
    print(f'  Block {b.start_offset}: {[i.opname for i in b.instructions]} succ={[s.start_offset for s in b.successors]}')

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
for r in regions:
    if isinstance(r, LoopRegion):
        print(f'\nLoop: entry={r.entry.start_offset}, cond={r.condition_block.start_offset if r.condition_block else None}, header={r.header_block.start_offset if r.header_block else None}')
        print(f'  body={[b.start_offset for b in r.body_blocks]}, else={[b.start_offset for b in r.else_blocks]}')
        hdr = r.header_block
        if hdr:
            cs = list(hdr.conditional_successors)
            print(f'  header cond_succs={[s.start_offset for s in cs]}')
            li = hdr.get_last_instruction()
            print(f'  header last op={li.opname if li else None}')
