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
fn = find(marshal.loads(open(PYC, 'rb').read()[16:]), 'clock_worker')
cfg = build_cfg(fn); an = RegionAnalyzer(cfg); an.analyze()
def o(x): return getattr(x, 'start_offset', x)
def L(v): return [] if not v else sorted(o(z) for z in v)
entries = {}
for r in an.regions:
    entries.setdefault(o(r.entry), []).append('%s@%d' % (type(r).__name__, o(r.entry)))
block_owner = {}
for b, r in an.block_to_region.items():
    block_owner.setdefault(o(b), []).append('%s@%d' % (type(r).__name__, o(r.entry)))
print('--- full elif_final_else sets, flagged by region-entry status ---')
for r in an.regions:
    fe = L(getattr(r, 'elif_final_else', None))
    if not fe: continue
    if not (7000 <= o(r.entry) <= 9300): continue
    ents = [x for x in fe if x in entries]
    print('CHAIN @%d fe_n=%d entries_in_fe=%d %s' % (
        o(r.entry), len(fe), len(ents), [(x, entries[x]) for x in ents]))
    print('   fe=%s' % fe)
    if o(r.entry) in (7186, 7634):
        for x in fe:
            b = [bb for bb in cfg.get_blocks_in_order() if o(bb) == x][0]
            ins = list(b.instructions)
            print('   fe@%-5d n=%-3d tail=%-26s owner=%s pred_outside_fe=%s' % (
                x, len(ins), ins[-1].opname if ins else '-', block_owner.get(x, ['-']),
                [o(p) for p in (getattr(b, 'predecessors', []) or []) if o(p) not in fe]))
print('--- dropped span 7972..8586 total instrs ---')
tot = 0
for b in cfg.get_blocks_in_order():
    if 7972 <= o(b) <= 8586: tot += len(list(b.instructions))
print('instrs_in_span=%d' % tot)
