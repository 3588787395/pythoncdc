"""Census rig R91 #2 — true ownership + why the while-condition boolop chain misses L2."""
import dis, marshal, sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import LoopRegion, IfRegion, BoolOpRegion, Region

PYC = (r'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/'
       'IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc')


def find(c, name):
    for k in c.co_consts:
        if hasattr(k, 'co_code'):
            if k.co_name == name:
                return k
            g = find(k, name)
            if g is not None:
                return g


code = marshal.loads(open(PYC, 'rb').read()[16:])
tgt = find(code, '_sync_worker')
cfg = build_cfg(tgt)
gen = RegionASTGenerator(cfg, top_level_code=None)
an = gen.region_analyzer
tops = an.analyze()

seen = set()
def walk(r, depth, out):
    if id(r) in seen:
        return
    seen.add(id(r))
    out.append((r, depth))
    for ch in r.children:
        walk(ch, depth + 1, out)


flat = []
for r in tops:
    walk(r, 0, flat)
print('unique regions=%d (analyze() top-level=%d)' % (len(flat), len(tops)))

# --- true single owner per block ---
print('\n=== A. block_to_region ownership 230..1214 ===')
for off in sorted(cfg.blocks):
    if not (230 <= off <= 1214):
        continue
    b = cfg.blocks[off]
    o = an.block_to_region.get(b)
    term = b.instructions[-1] if b.instructions else None
    print('  @%-6d n=%-4d owner=%-14s entry=%-6s term=%-30s' % (
        off, len(b.instructions), type(o).__name__ if o else 'None',
        o.entry.start_offset if o and o.entry else '-',
        term.opname if term else '-'))

print('\n=== B. region tree (dedup) ===')
for r, d in flat:
    pad = '    ' * d
    extra = ''
    if isinstance(r, LoopRegion):
        extra = ' hdr=@%s cond=@%s be=@%s be_set=%s wt=%s chain=%s' % (
            r.header_block.start_offset if r.header_block else '-',
            r.condition_block.start_offset if r.condition_block else '-',
            r.back_edge_block.start_offset if r.back_edge_block else '-',
            sorted(x.start_offset for x in r.back_edge_blocks),
            r.is_while_true,
            [x.start_offset for x in r.condition_chain_blocks])
    print('  %s%s entry=@%s%s' % (pad, type(r).__name__,
          r.entry.start_offset if r.entry else '-', extra))

print('\n=== C. _detect_while_condition_boolop_chain on L2 condition_block ===')
L2 = None
for r, d in flat:
    if isinstance(r, LoopRegion) and r.header_block and r.header_block.start_offset == 704:
        L2 = r
        break
if L2 is None:
    print('  L2 not found!')
else:
    cb = L2.condition_block
    print('  L2 found: entry=@%s cond=@%s body=%s' % (
        L2.entry.start_offset, cb.start_offset if cb else None,
        sorted(b.start_offset for b in L2.body_blocks)))
    if cb is not None:
        ch = an._detect_while_condition_boolop_chain(cb, L2)
        print('  chain=%s' % ([(b.start_offset, op) for b, op in ch] if ch else ch))
    print('  L2 metadata keys=%s' % sorted(L2.metadata.keys()))
    for k, v in sorted(L2.metadata.items()):
        if 'bool' in k or 'chain' in k or 'cond' in k or 'back' in k:
            print('    meta[%s]=%s' % (k, repr(v)[:200]))
