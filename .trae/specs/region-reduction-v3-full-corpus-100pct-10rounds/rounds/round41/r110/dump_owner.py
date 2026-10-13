"""dump_owner.py — read-only: who owns the chain-tail blocks now, and what the parent looks like.

usage: python -X utf8 dump_owner.py [LO] [HI]
"""
import marshal
import sys
import types

sys.path.insert(0, '.')
from core.cfg import build_cfg                     # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402


def find(c, n):
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            if k.co_name == n:
                return k
            r = find(k, n)
            if r:
                return r


PYC = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc'
LO = int(sys.argv[1]) if len(sys.argv) > 1 else 7400
HI = int(sys.argv[2]) if len(sys.argv) > 2 else 9250

fn = find(marshal.loads(open(PYC, 'rb').read()[16:]), 'clock_worker')
cfg = build_cfg(fn)
an = RegionAnalyzer(cfg)
an.analyze()


def o(x):
    return getattr(x, 'start_offset', x)


def L(v):
    return [] if not v else sorted(o(z) for z in v)


bl = {o(b): b for b in cfg.get_blocks_in_order()}
owners = {}
for b, r in an.block_to_region.items():
    owners.setdefault(o(b), []).append('%s@%d' % (type(r).__name__, o(r.entry)))

print('--- ownership of %d..%d ---' % (LO, HI))
unowned = []
for s in sorted(bl):
    if not (LO <= s <= HI):
        continue
    ow = owners.get(s, ['UNOWNED'])
    if ow == ['UNOWNED']:
        unowned.append(s)
    ins = list(bl[s].instructions)
    print('@%-5d n=%-3d tail=%-28s owner=%s succ=%s preds=%s' % (
        s, len(ins), (ins[-1].opname if ins else '-'), ow,
        L(getattr(bl[s], 'successors', [])), L(getattr(bl[s], 'predecessors', []))))
print('UNOWNED n=%d: %s' % (len(unowned), unowned))

print('--- regions touching the range ---')
for r in an.regions:
    bs = L(getattr(r, 'blocks', []))
    hit = [x for x in bs if LO <= x <= HI]
    if not hit:
        continue
    print('%s@%d nblk=%-3d hit=%-3d(%d..%d) cond=%s merge=%s hdr=%s then=%s else=%s fe_n=%d fe=%s' % (
        type(r).__name__, o(r.entry), len(bs), len(hit), hit[0], hit[-1],
        o(getattr(r, 'condition_block', None) or 0), o(getattr(r, 'merge_block', None) or 0),
        o(getattr(r, 'header_block', None) or 0),
        L(getattr(r, 'then_blocks', None))[:6], L(getattr(r, 'else_blocks', None))[:6],
        len(getattr(r, 'elif_final_else', None) or []), L(getattr(r, 'elif_final_else', None))[:6]))
print('--- region list (all, by entry) ---')
for r in sorted(an.regions, key=lambda x: o(x.entry)):
    print('  %-22s@%-6s nblk=%-3d exit=%s' % (type(r).__name__, o(r.entry),
                                              len(getattr(r, 'blocks', []) or []), o(getattr(r, 'exit', None) or 0)))
