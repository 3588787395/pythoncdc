"""R35 read-only driver: does the loop-header walk produce the STORE_ATTR statement?

Wraps RegionASTGenerator._loop_process_header_instructions from OUTSIDE (no repo edit, no CFG/analyzer
read inside the pipeline - only counts the caller's statement list before/after) and separately calls
_build_attr_assign directly on the fused header block's instruction prefix, so the two possible loss
points - "the walk never appends" vs "the caller drops it later" - are told apart by measurement.

usage: python -X utf8 probe_r35_header.py <pyc-rel-to-site-packages> <unit-co-name> <header-offset>
"""
import marshal
import os
import sys
import types

ROOT = r'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg import build_cfg                                     # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator        # noqa: E402

rel, unit, hoff = sys.argv[1], sys.argv[2], int(sys.argv[3])
pyc = os.path.join(ROOT, 'site-packages', rel)
co_top = marshal.loads(open(pyc, 'rb').read()[16:])


def find(co, name):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                return c
            r = find(c, name)
            if r is not None:
                return r
    return None


target = find(co_top, unit) or co_top

# --- 1. direct call of the builder on the instruction prefix ---
cfg = build_cfg(target)
blk = cfg.get_block_by_offset(hoff)
print('header block @%s instructions=%d' % (hoff, len(blk.instructions)))
for i in blk.instructions:
    print('   @%-5d %-28s %s' % (i.offset, i.opname, i.argval))

gen = RegionASTGenerator(cfg, top_level_code=target if target.co_name == '<module>' else None)
prefix = [i for i in blk.instructions]
sa = [n for n, i in enumerate(prefix) if i.opname == 'STORE_ATTR']
print('\nSTORE_ATTR at index %s' % sa)
if sa:
    upto = prefix[:sa[0] + 1]
    for fname in ('_build_attr_assign',):
        f = getattr(gen, fname, None)
        try:
            r = f(upto)
        except Exception as e:
            r = 'EXC %s' % e
        print('%s(prefix) -> %s' % (fname, (str(r)[:300] if r is not None else 'None')))

# --- 2. wrapped walk: does it append a statement for this block? ---
records = []
orig = RegionASTGenerator._loop_process_header_instructions


def wrapper(self, block, region, body_stmts):
    before = len(body_stmts)
    r = orig(self, block, region, body_stmts)
    after = len(body_stmts)
    records.append((block.start_offset, before, after,
                    [s.get('type') for s in body_stmts[before:after]]))
    return r


RegionASTGenerator._loop_process_header_instructions = wrapper
ast_dict = gen.generate()
print('\nwalk records (block, before, after, new stmt types):')
for rec in records:
    print('   ', rec)
print('header block present in records: %s'
      % any(r[0] == hoff for r in records))
