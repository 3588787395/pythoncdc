import py_compile, sys, os, marshal
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, WithRegion

tf = 'test_w03_multi_with.py'
pyc = tf+'c'
py_compile.compile(tf, cfile=pyc, doraise=True)
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)
func_code = code.co_consts[0]
cfg = CFGBuilder().build(func_code)
ra = RegionAnalyzer(cfg)
ra.analyze()

for region in ra.regions:
    if isinstance(region, WithRegion):
        print(f'WithRegion: entry={region.entry.start_offset}')
        print(f'  body_offset_start={region.body_offset_start}, body_offset_end={region.body_offset_end}')
        print(f'  with_blocks={[b.start_offset for b in region.with_blocks]}')
        print(f'  target={region.target}')
        print(f'  items={[(len(instrs), target) for instrs, target in region.items]}')
        blocks_sorted = sorted(region.blocks, key=lambda b: b.start_offset)
        print(f'  all blocks={[b.start_offset for b in blocks_sorted]}')
        
        body_end_offset = region.body_offset_end
        print(f'\n  Post-with analysis (body_end_offset={body_end_offset}):')
        for blk in blocks_sorted:
            if blk.start_offset < body_end_offset:
                continue
            in_wb = blk in region.with_blocks
            is_entry = blk == region.entry
            is_cleanup = ra._is_with_exit_cleanup(blk)
            role = ra.block_roles.get(blk)
            has_bw = any(i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for i in blk.instructions)
            instrs_summary = [(i.offset, i.opname) for i in blk.instructions if i.opname not in ('CACHE',)]
            print(f'    block {blk.start_offset}: in_wb={in_wb}, is_entry={is_entry}, is_cleanup={is_cleanup}, role={role}, has_bw={has_bw}')
            print(f'      instrs={instrs_summary[:8]}...')

if os.path.exists(pyc): os.remove(pyc)
