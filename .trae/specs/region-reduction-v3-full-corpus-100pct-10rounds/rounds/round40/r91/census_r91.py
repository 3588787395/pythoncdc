"""Census rig R91: region structure around the _sync_worker loop.

usage: python -X utf8 census_r91.py [low high]
Read-only: builds the CFG + runs RegionAnalyzer.analyze() on the _sync_worker
code object exactly as the production pipeline does, then prints. Nothing here
mutates analyzer state.
"""
import dis
import marshal
import sys

sys.path.insert(0, '.')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = (r'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/'
       'IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc')

LOW = int(sys.argv[1]) if len(sys.argv) > 1 else 704
HIGH = int(sys.argv[2]) if len(sys.argv) > 2 else 1210


def find(c, name):
    for const in c.co_consts:
        if hasattr(const, 'co_code'):
            if const.co_name == name:
                return const
            got = find(const, name)
            if got is not None:
                return got
    return None


code = marshal.loads(open(PYC, 'rb').read())[16:] if False else None
raw = open(PYC, 'rb').read()
code = marshal.loads(raw[16:])
tgt = find(code, '_sync_worker')
print('code object: %s instr-count-in-dis=%d' % (tgt.co_name, len(list(dis.get_instructions(tgt)))))

cfg = build_cfg(tgt)
gen = RegionASTGenerator(cfg, top_level_code=tgt if tgt.co_name == '<module>' else None)
an = gen.region_analyzer
regions = an.analyze()
blocks = list(cfg.blocks.values())
bysoff = {}
for b in blocks:
    bysoff[b.start_offset] = b
print('cfg blocks=%d regions=%d' % (len(blocks), len(regions)))


def term(b):
    for ins in reversed(b.instructions):
        if ins.opname in ('NOP', 'CACHE', 'PRECALL', 'EXTENDED_ARG'):
            continue
        return ins
    return None


def tgt_of(ins):
    if ins is None:
        return None
    if ins.opname.startswith('JUMP') or ins.opname.startswith('POP_JUMP') or ins.opname in ('FOR_ITER', 'SEND'):
        return ins.argval if isinstance(ins.argval, int) else None
    return None


# ─── 1. every block whose terminator is a BACKWARD jump ─────────────────────
print('\n=== [1] BACKWARD-jump terminators (block_start -> target) ===')
back = {}
for b in sorted(blocks, key=lambda x: x.start_offset):
    t = term(b)
    if t is None:
        continue
    if 'BACKWARD' not in t.opname and t.opname not in ('JUMP_LOOP',):
        continue
    dst = tgt_of(t)
    if dst is None or dst >= b.start_offset and t.opname != 'JUMP_BACKWARD':
        pass
    back.setdefault(dst, []).append((b.start_offset, t.opname, len(b.instructions)))
    print('  @%-6d n=%-4d %-34s -> @%s' % (b.start_offset, len(b.instructions), t.opname, dst))
print('\n  distinct backward targets: %d' % len(back))
for dst in sorted(back):
    if len(back[dst]) > 1:
        print('  ** target @%s reached BACKWARD by %d distinct blocks: %s'
              % (dst, len(back[dst]), [(o, op) for o, op, n in back[dst]]))

# ─── 2. target @704 style: who lands on the window offsets ──────────────────
print('\n=== [2] all predecessors (forward+backward) of blocks in [%d,%d] ===' % (LOW, HIGH))
for so in sorted(bysoff):
    if not (LOW <= so <= HIGH):
        continue
    b = bysoff[so]
    t = term(b)
    ps = []
    for p in b.predecessors:
        pt = term(p)
        kind = 'BWD' if (pt is not None and 'BACKWARD' in pt.opname) else 'FWD'
        ps.append((p.start_offset, kind, pt.opname if pt else '?'))
    print('  @%-6d n=%-4d term=%-32s -> @%-6s preds=%s'
          % (so, len(b.instructions), t.opname if t else '?',
             tgt_of(t) if t else None, sorted(ps)))

# ─── 3. region ownership of the window ─────────────────────────────────────
print('\n=== [3] regions that own any block start in [%d,%d] ===' % (LOW, HIGH))


def dump_region(r, depth=0, tag=''):
    pad = '  ' * depth
    kind = type(r).__name__
    ent = r.entry.start_offset if r.entry else None
    line = '%s%s %sentry=@%s' % (pad, tag, kind, ent)
    if isinstance(r, type(None)):
        return
    print(line)
    hdr = getattr(r, 'header_block', None)
    cond = getattr(r, 'condition_block', None)
    meb = getattr(r, 'merge_block', None) or getattr(r, 'exit', None)
    if hdr is not None:
        print('%s   header=@%s cond=@%s merge=@%s' % (pad, hdr.start_offset,
              cond.start_offset if cond else None,
              meb.start_offset if meb else None))
    beb = getattr(r, 'back_edge_block', None)
    bebs = getattr(r, 'back_edge_blocks', None)
    if beb is not None or bebs:
        print('%s   back_edge_block=@%s back_edge_blocks=%s' % (pad,
              beb.start_offset if beb else None,
              sorted(b.start_offset for b in (bebs or ())) if bebs else '[]'))
    if getattr(r, 'is_while_true', False):
        print('%s   is_while_true=True' % pad)
    crb = getattr(r, 'condition_recheck_blocks', None)
    if crb:
        print('%s   cond_recheck=%s' % (pad, sorted(b.start_offset for b in crb)))
    ccb = getattr(r, 'condition_chain_blocks', None)
    if ccb:
        print('%s   cond_chain=%s' % (pad, [b.start_offset for b in ccb]))
    eb = getattr(r, 'else_blocks', None)
    if eb:
        print('%s   else_blocks=%s' % (pad, sorted(b.start_offset for b in eb)))
    bb = getattr(r, 'body_blocks', None)
    if bb:
        print('%s   body=%s' % (pad, sorted(b.start_offset for b in bb)))
    if getattr(r, 'has_break', False):
        print('%s   has_break=True break_blocks=%s' % (pad,
              sorted(b.start_offset for b in getattr(r, 'break_blocks', ()))))
    for ch in r.children:
        dump_region(ch, depth + 1)


allregions = []


def walk(r):
    allregions.append(r)
    for ch in r.children:
        walk(ch)


for r in regions:
    walk(r)
print('total regions incl children=%d' % len(allregions))

owners = {}
for r in allregions:
    bs = set()
    for a in ('blocks', 'body_blocks', 'else_blocks', 'init_blocks'):
        v = getattr(r, a, None)
        if v:
            bs.update(v)
    for a in ('condition_block', 'header_block', 'back_edge_block'):
        v = getattr(r, a, None)
        if v:
            bs.add(v)
    for a in ('back_edge_blocks', 'condition_recheck_blocks'):
        v = getattr(r, a, None)
        if v:
            bs.update(v)
    for b in bs:
        owners.setdefault(b.start_offset, []).append(r)

for so in sorted(owners):
    if LOW <= so <= HIGH:
        print('\n  block @%s owned by %d region(s):' % (so, len(owners[so])))
        for r in owners[so]:
            print('     %s entry=%s type=%s' % (type(r).__name__,
                  r.entry.start_offset if r.entry else None, getattr(r, 'region_type', None)))

print('\n=== [4] every LOOP region (whole unit) ===')
for r in allregions:
    if type(r).__name__ == 'LoopRegion':
        print('\n  LOOP entry=@%s' % (r.entry.start_offset if r.entry else None))
        dump_region(r, 1, '  ')
