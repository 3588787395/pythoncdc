import sys
sys.path.insert(0, '.')
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.cfg_builder import CFGBuilder
import marshal, types

with open('site-packages/IQCommon/util/replace_utils.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'decrypt_database_url':
        func_code = const
        break

builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

for r in regions:
    if hasattr(r, 'container_type'):
        if hasattr(r, 'entry') and hasattr(r.entry, 'offset'):
            entry_off = r.entry.offset
        else:
            entry_off = r.entry
        if entry_off != 292:
            continue
        mb = r.merge_block
        if mb:
            print('merge_block offset=%s end=%s' % (mb.offset, mb.end_offset))
            print('merge_block instructions:')
            for i in mb.instructions:
                print('  %s %s %s %s' % (i.offset, i.opname, i.arg, i.argval))
        cb = r.cond_block
        if cb:
            print('cond_block offset=%s end=%s' % (cb.offset, cb.end_offset))
        tb = r.true_block
        fb = r.false_block
        print('true_block=%s false_block=%s' % (tb, fb))
        print('blocks in region:')
        for b in r.blocks:
            if hasattr(b, 'id'):
                print('  Block %s offset=%s-%s instrs=%s' % (b.id, b.offset, b.end_offset, len(b.instructions)))
            else:
                print('  Block offset=%s-%s instrs=%s' % (b.offset, b.end_offset, len(b.instructions)))

# Also find Block 6 specifically
for blk in cfg.blocks:
    if hasattr(blk, 'offset') and blk.offset == 400:
        print('\nBlock at offset 400:')
        print('  offset=%s end=%s' % (blk.offset, blk.end_offset))
        for i in blk.instructions:
            print('  %s %s %s %s' % (i.offset, i.opname, i.arg, i.argval))
