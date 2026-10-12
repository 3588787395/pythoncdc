"""Read-only premise dump: chain @7186 / parent arm @7216 / candidate @7248."""
import marshal, sys
sys.path.insert(0, 'D:/Temp/r83')
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = "D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc"
co = marshal.loads(open(PYC, 'rb').read()[16:])

def find(c, n):
    for x in c.co_consts:
        if isinstance(x, type(c)) and x.co_name == n:
            return x
        if isinstance(x, type(c)):
            r = find(x, n)
            if r:
                return r

cw = find(co, 'clock_worker')
cfg = build_cfg(cw)
gen = RegionASTGenerator(cfg, parent_code=cw, top_level_code=None)
gen.generate()
off = lambda b: getattr(b, 'start_offset', b if isinstance(b, int) else None)
def offs(seq):
    out = []
    for x in seq or []:
        if isinstance(x, list):
            out.append([off(y) for y in x])
        else:
            out.append(off(x))
    return out

byc = {}
for r in gen.regions:
    c = off(getattr(r, 'condition_block', None))
    if c is not None:
        byc.setdefault(c, []).append(r)

for c in (7186, 7216, 7248, 7270):
    for r in byc.get(c, []):
        print('== %s cond=%s type=%s' % (type(r).__name__, c, r.region_type))
        for f in ('then_blocks', 'else_blocks', 'elif_conditions', 'elif_bodies', 'elif_final_else', 'merge_block'):
            if hasattr(r, f):
                v = getattr(r, f)
                print('   %-16s %s' % (f, offs(v) if isinstance(v, list) else off(v)))
        print('   IBC %s' % {k: (v.get('op'), [off(b) for b in v.get('blocks', [])]) for k, v in (getattr(r, 'inline_boolop_chains', None) or {}).items()})

chain = [r for r in byc.get(7186, []) if getattr(r, 'elif_conditions', None)]
parent = byc.get(7216, [])
if chain and parent:
    ch = chain[0]; pa = parent[0]
    cond = off(ch.elif_conditions[0])
    cand = [r for r in byc.get(cond, [])]
    # successors of @7248
    b7248 = ch.elif_conditions[0]
    succs = sorted(off(b) for b in b7248.successors)
    false_exit = None
    for s in b7248.successors:
        pass
    print('candidate @%s successors=%s' % (cond, succs))
    fe = succs[-1] if succs else None
    print('elif_final_else size=%d' % len(ch.elif_final_else))
    print('parent then_blocks size=%d' % len(pa.then_blocks))
    print('@7492 in parent.then_blocks=%s  in chain.elif_final_else=%s' % (
        7492 in offs(pa.then_blocks), 7492 in offs(ch.elif_final_else)))
