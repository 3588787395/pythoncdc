"""READ-ONLY probe: dump IfRegion.inline_boolop_chains + child region pointers for the
@7164..@7602 family in clock_worker, on the CURRENT mirror bytes.

usage: python -X utf8 work/probe_ibc.py
"""
import dis
import marshal
import sys

REPO = r"D:/Temp/r76"
sys.path.insert(0, REPO)
PYC = (r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/"
       r"IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc")
UNIT = "clock_worker"
WANT = (7164, 7186, 7216, 7248, 7270, 7492, 7582)

from core.cfg import build_cfg                                             # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer                        # noqa: E402

CO = type(compile("", "", "exec"))


def gather(c, acc):
    acc.append(c)
    for cst in c.co_consts:
        if isinstance(cst, CO):
            gather(cst, acc)


def win(b):
    if b is None or not getattr(b, 'instructions', None):
        return "None"
    i = b.instructions
    return "@%d..@%d(%d)" % (i[0].offset, i[-1].offset, len(i))


def offs(bl):
    return [b.instructions[0].offset for b in (bl or []) if getattr(b, 'instructions', None)]


code = marshal.loads(open(PYC, "rb").read()[16:])
acc = []
gather(code, acc)
target = max([c for c in acc if c.co_name == UNIT], key=lambda c: len(c.co_code))
cfg = build_cfg(target)
an = RegionAnalyzer(cfg)
regions = an.analyze()
by_off = {}
for b in cfg.blocks.values() if isinstance(cfg.blocks, dict) else cfg.blocks:
    if getattr(b, 'instructions', None):
        by_off[b.instructions[0].offset] = b


def _e(r):
    b = (getattr(r, 'entry_block', None) or getattr(r, 'header_block', None)
         or getattr(r, 'condition_block', None))
    return b.instructions[0].offset if b is not None and b.instructions else -1


print("=== regions whose condition_block/then touch %s" % (WANT,))
for r in regions:
    cb = getattr(r, 'condition_block', None)
    cbo = cb.instructions[0].offset if cb is not None and cb.instructions else -1
    touched = set(WANT) & (set(offs(getattr(r, 'then_blocks', None)))
                           | set(offs(getattr(r, 'else_blocks', None)))
                           | {cbo})
    if not touched:
        continue
    print("-- %s cond=%s then=%s else=%s merge=%s parent=%s" % (
        type(r).__name__, win(cb), offs(getattr(r, 'then_blocks', None)),
        offs(getattr(r, 'else_blocks', None)), win(getattr(r, 'merge_block', None)),
        _e(getattr(r, 'parent', None)) if getattr(r, 'parent', None) else None))
    ibc = getattr(r, 'inline_boolop_chains', None) or {}
    for k, v in ibc.items():
        head = None
        for b in by_off.values():
            if id(b) == k:
                head = b.instructions[0].offset
        print("     ibc key-block=@%s op=%r blocks=%s" % (
            head, v.get('op'), offs(v.get('blocks'))))
    for f in ('child_regions', 'nested_regions', 'regions'):
        v = getattr(r, f, None)
        if v:
            print("     %s=%s" % (f, [(type(x).__name__, _e(x)) for x in v]))
    # any other dict-ish attrs
    for a in dir(r):
        if a.startswith('_') or a in ('inline_boolop_chains',):
            continue
        try:
            val = getattr(r, a)
        except Exception:
            continue
        if isinstance(val, dict) and val:
            print("     attr %s = %s" % (a, {k: (v if not hasattr(v, 'instructions') else 'BLK')
                                             for k, v in list(val.items())[:4]}))

print()
print("=== per-block region ownership / role for %s" % (WANT,))
for off in WANT:
    b = by_off.get(off)
    if b is None:
        print("@%-6d no block" % off)
        continue
    r = an.get_region_for_block(b)
    last = b.get_last_instruction()
    print("@%-6d win=%s succ=%s preds=%s role=%s owner=%s@%s last=%s->%s" % (
        off, win(b), offs(b.successors), offs(b.predecessors), an.get_block_role(b),
        type(r).__name__ if r else None, _e(r) if r else '-',
        last.opname if last else None, last.argval if last else None))
