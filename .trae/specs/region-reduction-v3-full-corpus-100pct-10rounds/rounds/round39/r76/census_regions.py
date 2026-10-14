"""Read-only region census for realtime_event_source.clock_worker on the CURRENT mirror bytes.

usage: python -X utf8 work/census_regions.py [block offsets ...]
"""
import dis
import marshal
import sys

REPO = r"D:/Temp/r76"
sys.path.insert(0, REPO)
PYC = (r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/"
       r"IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc")
UNIT = "clock_worker"

from core.cfg import build_cfg                                             # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer                        # noqa: E402

CO = type(compile("", "", "exec"))
WANTED = [int(x) for x in sys.argv[1:]] or [6762, 6778, 7224, 7252, 7270, 7310, 9194, 9210]


def gather(c, acc):
    acc.append(c)
    for cst in c.co_consts:
        if isinstance(cst, CO):
            gather(cst, acc)


def win(b):
    if b is None or not b.instructions:
        return "None"
    i = b.instructions
    return "@%d..@%d(%d)" % (i[0].offset, i[-1].offset, len(i))


def offs(bl):
    return sorted(b.instructions[0].offset for b in (bl or []) if b.instructions)


code = marshal.loads(open(PYC, "rb").read()[16:])
acc = []
gather(code, acc)
target = max([c for c in acc if c.co_name == UNIT], key=lambda c: len(c.co_code))
print("picked clock_worker firstlineno=%d instrs=%d" % (
    target.co_firstlineno, sum(1 for _ in dis.get_instructions(target))))

cfg = build_cfg(target)
an = RegionAnalyzer(cfg)
regions = an.analyze()
print("regions=%d blocks=%d" % (len(regions), len(cfg.blocks)))


def _e(r):
    b = (getattr(r, 'entry_block', None) or getattr(r, 'header_block', None)
         or getattr(r, 'condition_block', None))
    return b.instructions[0].offset if b is not None and b.instructions else -1


for r in sorted(regions, key=_e):
    t = type(r).__name__
    parts = [t, win(getattr(r, 'entry_block', None) or getattr(r, 'header_block', None))]
    for f in ('header_block', 'condition_block', 'body_blocks', 'then_blocks', 'else_blocks',
              'merge_block', 'back_edge_block', 'exit_blocks', 'boolop_blocks'):
        if hasattr(r, f):
            v = getattr(r, f)
            parts.append("%s=%s" % (f, offs(v) if isinstance(v, list) else win(v)))
    print("  " + " ".join(str(p) for p in parts))

print()
print("=== ownership of the loss blocks")
ALL_BLOCKS = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
by_off = {}
for b in ALL_BLOCKS:
    if b.instructions:
        by_off[b.instructions[0].offset] = b
for off in WANTED:
    b = by_off.get(off)
    if b is None:
        print("  @%-6d no block starts here" % off)
        continue
    r = an.get_region_for_block(b)
    last = b.get_last_instruction()
    print("  @%-6d win=%s succ=%s preds=%s role=%s region=%s last=%s argval=%s" % (
        off, win(b),
        [(s.instructions[0].offset if s.instructions else None) for s in (b.successors or [])],
        [(p.instructions[0].offset if p.instructions else None) for p in (b.predecessors or [])],
        an.get_block_role(b),
        type(r).__name__ + ' ' + win(getattr(r, 'entry_block', None) or getattr(r, 'header_block', None)),
        last.opname if last else None, last.argval if last else None))
