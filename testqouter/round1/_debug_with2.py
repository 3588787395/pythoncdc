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
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print(f'=== ALL BLOCKS ===')
for offset, block in sorted(cfg.blocks.items()):
    instrs = [f'{i.opname}({getattr(i, "argval", "")})' for i in block.instructions]
    succs = [s.start_offset for s in block.successors]
    exc_succs = [s.start_offset for s in block.exception_successors]
    print(f'  Block offset={block.start_offset}: instrs={instrs[:5]}...')
    print(f'    succs={succs}, exc_succs={exc_succs}')

print(f'\n=== WITH REGIONS ===')
for region in regions:
    if isinstance(region, WithRegion):
        print(f'WithRegion entry={region.entry.start_offset}')
        print(f'  with_blocks={[b.start_offset for b in region.with_blocks]}')
        print(f'  blocks=sorted({sorted(b.start_offset for b in region.blocks)})')
        print(f'  target={region.target}')
        print(f'  items={[(len(instrs), tgt) for instrs, tgt in region.items]}')
        print(f'  body_offset_start={region.body_offset_start}')
        print(f'  body_offset_end={region.body_offset_end}')
        
        # Check post_with blocks
        body_end_offset = region.body_offset_end if region.body_offset_end > 0 else 0
        print(f'  body_end_offset={body_end_offset}')
        for blk in sorted(region.blocks, key=lambda b: b.start_offset):
            if blk.start_offset < body_end_offset:
                continue
            if blk in region.with_blocks or blk == region.entry:
                continue
            blk_instrs = [f'{i.opname}({getattr(i, "argval", "")})' for i in blk.instructions]
            role = analyzer.get_block_role(blk)
            is_cleanup = analyzer._is_with_exit_cleanup(blk)
            has_bw = any(i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for i in blk.instructions)
            print(f'    Post block offset={blk.start_offset}: role={role}, is_cleanup={is_cleanup}, has_bw={has_bw}')
            print(f'      instrs={blk_instrs[:8]}...')
