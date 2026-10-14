import marshal, sys, types
sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

def find(c, n):
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            if k.co_name == n: return k
            r = find(k, n)
            if r: return r

PYC = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc'
LO = int(sys.argv[1]); HI = int(sys.argv[2])
fn = find(marshal.loads(open(PYC, 'rb').read()[16:]), 'clock_worker')
cfg = build_cfg(fn); an = RegionAnalyzer(cfg); an.analyze()
def o(x): return getattr(x, 'start_offset', x)
def L(v): return [] if not v else sorted(o(z) for z in v)
bl = {o(b): b for b in cfg.get_blocks_in_order()}
print('--- block census %d..%d: owner / n_instr / tail / succ / preds ---' % (LO, HI))
for s in sorted(bl):
    if not (LO <= s <= HI): continue
    b = bl[s]; ins = list(b.instructions)
    r = an.block_to_region.get(b)
    print('@%d n=%-3d tail=%-28s owner=%-22s succ=%s preds=%s' % (
        s, len(ins), (ins[-1].opname if ins else '-'),
        ('%s@%d' % (type(r).__name__, o(r.entry))) if r else 'UNOWNED',
        L(getattr(b, 'successors', [])), L(getattr(b, 'predecessors', []))))
print('--- regions with any block in %d..%d ---' % (LO, HI))
for r in an.regions:
    bs = L(getattr(r, 'blocks', []))
    hit = [x for x in bs if LO <= x <= HI]
    if not hit: continue
    print('%s@%d hdr=%s cond=%s merge=%s nblk=%d inrange=%d(%d..%d) elif_c=%s elif_b=%s fe_n=%d fe=%s' % (
        type(r).__name__, o(r.entry), o(getattr(r, 'header_block', None) or 0),
        o(getattr(r, 'condition_block', None) or 0), o(getattr(r, 'merge_block', None) or 0),
        len(bs), len(hit), hit[0], hit[-1], L(getattr(r, 'elif_conditions', None)),
        [len(x) for x in (getattr(r, 'elif_bodies', None) or [])], len(getattr(r, 'elif_final_else', None) or []),
        L(getattr(r, 'elif_final_else', None))[:8]))
