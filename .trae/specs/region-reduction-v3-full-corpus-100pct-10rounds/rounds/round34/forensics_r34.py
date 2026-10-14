"""R34 forensics: compare the victim back-edge block against an over-fire site.

usage: python -X utf8 forensics_r34.py <pyc-rel-to-site-packages> <unit-co-name> <block-offset>

Prints, for one code object, everything the generator could read at the suppression
decision point about one back-edge block: its own instructions, its predecessors and
their terminators, its region chain (entry/merge/membership), the enclosing loop's own
fields (header, body offsets, declared back-edge blocks), and the blocks the block's
jump skips together with who owns them. Read-only; no generation, no repo writes.
"""
import dis
import marshal
import os
import sys
import types

SPEC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SPEC, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from core.cfg import build_cfg                                        # noqa: E402
from core.cfg.region_analyzer import (RegionAnalyzer, IfRegion,      # noqa: E402
                                      LoopRegion, TryExceptRegion)

SITE = os.path.join(ROOT, 'site-packages')
DROP = ('NOP', 'CACHE', 'EXTENDED_ARG', 'RESUME')


def find(co, name):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                return c
            r = find(c, name)
            if r is not None:
                return r
    return None


def term(block):
    for i in reversed(block.instructions):
        if i.opname in DROP:
            continue
        return i
    return None


def show(block, cfg, mark=''):
    t = term(block)
    print('   %sblk @%-6s n=%-3d term=%-28s %s'
          % (mark, block.start_offset, len(block.instructions),
             t.opname if t else '-', (t.argval if t.argval is not None else '') if t else ''))


def main():
    rel, unit, off = sys.argv[1], sys.argv[2], int(sys.argv[3])
    code = marshal.loads(open(os.path.join(SITE, rel), 'rb').read()[16:])
    co = find(code, unit)
    if co is None:
        sys.exit('unit %s not found in %s' % (unit, rel))
    cfg = build_cfg(co)
    az = RegionAnalyzer(cfg)
    regions = az.analyze()
    block = cfg.get_block_by_offset(off)
    if block is None:
        sys.exit('block @%d not found' % off)

    print('=== %s :: %s :: block @%d' % (rel, unit, off))
    print('-- block instructions:')
    for i in block.instructions:
        if i.opname in DROP:
            continue
        print('     @%-6d %-30s %s' % (i.offset, i.opname, i.argval if i.argval is not None else ''))
    print('-- predecessors:')
    for p in (block.predecessors or []):
        show(p, cfg, '   pred ')
        print('        role=%s' % az.get_block_role(p))
    print('-- successors:', [s.start_offset for s in (block.successors or [])])
    print('-- role of block:', az.get_block_role(block))

    print('-- region chain (innermost first):')
    r = az.get_region_for_block(block)
    depth = 0
    seen = set()
    while r is not None and id(r) not in seen:
        seen.add(id(r))
        extra = ''
        if isinstance(r, IfRegion):
            extra = 'entry=%s merge=%s then=%s else=%s' % (
                getattr(r, 'entry_block', None) and r.entry_block.start_offset,
                getattr(r, 'merge_block', None) and r.merge_block.start_offset,
                [b.start_offset for b in (r.then_blocks or [])],
                [b.start_offset for b in (r.else_blocks or [])])
        elif isinstance(r, LoopRegion):
            be = getattr(r, 'back_edge_block', None)
            bes = getattr(r, 'back_edge_blocks', None)
            extra = ('hdr=%s back_edge=%s back_edges=%s body=%s'
                     % (r.header_block and r.header_block.start_offset,
                        be and be.start_offset,
                        sorted(x.start_offset for x in (bes or [])),
                        sorted(b.start_offset for b in (r.body_blocks or []))))
        print('   %s%s %s' % ('  ' * depth, type(r).__name__, extra))
        print('      holds block: %s' % (block in (getattr(r, 'blocks', None) or [])))
        owner = r
        par = getattr(r, 'parent', None)
        r = par if par is not None else None
        depth += 1
        if depth > 8:
            break

    loop = None
    rr = az.get_region_for_block(block)
    while rr is not None:
        if isinstance(rr, LoopRegion):
            loop = rr
            break
        rr = getattr(rr, 'parent', None)
    if loop is None:
        for cand in regions:
            if isinstance(cand, LoopRegion) and block in (cand.body_blocks or []):
                loop = cand
                break
    if loop is None:
        print('-- no enclosing LoopRegion found')
        return

    print('-- enclosing loop @%s: blocks the jump skips:' % loop.header_block.start_offset)
    skipped = [b for b in (loop.body_blocks or [])
               if b.start_offset > block.start_offset]
    for b in sorted(skipped, key=lambda x: x.start_offset):
        show(b, cfg, '     skip ')
        print('        role=%s owner=%s' % (az.get_block_role(b),
                                            type(az.get_region_for_block(b)).__name__))
    hdr = loop.header_block
    print('-- who enters the header (back edges):')
    for p in (hdr.predecessors or []):
        show(p, cfg, '     hdrpred ')
        print('        role=%s owner=%s' % (az.get_block_role(p),
                                            type(az.get_region_for_block(p)).__name__))


if __name__ == '__main__':
    main()
