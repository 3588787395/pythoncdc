import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
os.chdir(r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1')

from pycdc import decompile_pyc
from pycdc.core.cfg.cfg_builder import CFGBuilder
from pycdc.core.cfg.region_analyzer import RegionAnalyzer
import dis

for tf in ['test_w03_multi_with.py', 'test_w04_nested_with.py']:
    pyc = tf + 'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)

    with open(tf) as f:
        code = compile(f.read(), tf, 'exec')
    func_code = code.co_consts[0]

    cfg = CFGBuilder().build(func_code)
    analyzer = RegionAnalyzer(cfg)

    print(f'=== {tf} CFG BLOCKS ===')
    for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
        instrs = [(i.offset, i.opname, i.argval) for i in block.instructions
                  if i.opname not in ('CACHE',)]
        has_bw = any(i.opname == 'BEFORE_WITH' for i in block.instructions)
        succ_offsets = [s.start_offset for s in block.successors]
        exc_succ_offsets = [s.start_offset for s in block.exception_successors]
        marker = ' ** BEFORE_WITH **' if has_bw else ''
        print(f'  Block {block.start_offset}: instrs={instrs}')
        print(f'    succs={succ_offsets} exc_succs={exc_succ_offsets}{marker}')

    print(f'\n=== {tf} WITH REGIONS ===')
    with_regions = analyzer._identify_with_regions()
    for wr in with_regions:
        entry_blocks = []
        for blk in sorted(wr.blocks, key=lambda b: b.start_offset):
            has_bw = any(i.opname == 'BEFORE_WITH' for i in blk.instructions)
            if has_bw:
                entry_blocks.append(blk.start_offset)
        print(f'  WithRegion: entry={wr.entry.start_offset}, '
              f'with_blocks={[b.start_offset for b in wr.with_blocks]}, '
              f'body_offset_start={wr.body_offset_start}, body_offset_end={wr.body_offset_end}, '
              f'entry_blocks={entry_blocks}, '
              f'items={[(len(instrs), target) for instrs, target in wr.items]}, '
              f'all_blocks={sorted(b.start_offset for b in wr.blocks)}')

    print()
    if os.path.exists(pyc):
        os.remove(pyc)
