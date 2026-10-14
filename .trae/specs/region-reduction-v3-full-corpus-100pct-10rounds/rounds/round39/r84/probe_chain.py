"""Read-only region probe for clock_worker @7186 chain on MIRROR bytes (base 30a4d7827122e165).

usage: python -X utf8 work/probe_chain.py
"""
import dis, marshal, os, sys

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)
PYC = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc"
UNIT = "clock_worker"
CO_RE = None
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, RegionType

CO = type(compile("", "", "exec"))


def gather(c, acc):
    acc.append(c)
    for cst in c.co_consts:
        if isinstance(cst, CO):
            gather(cst, acc)


def so(b):
    return b.start_offset if b is not None else None


def offs(bl):
    return sorted(b.start_offset for b in (bl or []) if b.instructions)


def last_info(b):
    if b is None or not b.instructions:
        return "None"
    li = b.get_last_instruction()
    return "%s arg=%s tgt=%s" % (li.opname, getattr(li, 'argval', None),
                                 li.target if hasattr(li, 'target') else '?')


code = marshal.loads(open(PYC, "rb").read()[16:])
acc = []
gather(code, acc)
target = max([c for c in acc if c.co_name == UNIT], key=lambda c: len(c.co_code))
cfg = build_cfg(target)
an = RegionAnalyzer(cfg)
regions = an.analyze()
by_off = {b.start_offset: b for b in cfg.blocks.values() if b.instructions}

# find IF_ELIF_CHAIN at 7186
for r in regions:
    if isinstance(r, IfRegion) and so(getattr(r, 'condition_block', None)) == 7186:
        print("=== IfRegion cond=7186 kind=", getattr(r, 'region_type', None))
        print(" then_blocks     ", offs(r.then_blocks))
        print(" elif_conditions ", offs(r.elif_conditions))
        print(" elif_bodies     ", [offs(x) for x in (r.elif_bodies or [])])
        ef = list(r.elif_final_else or [])
        print(" elif_final_else count=", len(ef), " first5=", [so(b) for b in ef[:5]], " last=", so(ef[-1]) if ef else None)
        print(" merge_block     ", so(r.merge_block), "last=", last_info(r.merge_block))
        print(" blocks count    ", len(r.blocks) if r.blocks else None)
        # arms: elif body arm and final-else arm exit targets
        for name, arm in [("elif_body[0]", (r.elif_bodies or [[]])[0]), ("final_else", ef)]:
            if arm:
                t = arm[-1]
                print("  arm", name, "tail block=", so(t), "exit=", last_info(t),
                      "succ=", [so(s) for s in (t.successors or [])])
        print(" elif_cond @7248 last=", last_info(by_off.get(7248)),
              "succ=", [so(s) for s in (by_off[7248].successors or [])] if 7248 in by_off else "?")

# loop context: is 7186 inside a LoopRegion?
print("\n=== loop regions containing 7186 ===")
for r in regions:
    if isinstance(r, LoopRegion):
        bs = {so(b) for b in (r.blocks or []) if b}
        if 7186 in bs or (getattr(r, 'body_blocks', None) and 7186 in {so(b) for b in r.body_blocks if b}):
            print(" LoopRegion entry=", so(getattr(r, 'entry_block', None) or getattr(r, 'header_block', None)),
                  "header=", so(getattr(r, 'header_block', None)), last_info(getattr(r, 'header_block', None)),
                  "back_edge_block=", so(getattr(r, 'back_edge_block', None)),
                  "back_edge_blocks=", offs(getattr(r, 'back_edge_blocks', None)),
                  "exit_blocks=", offs(getattr(r, 'exit_blocks', None)))

# what is @9206 and the loop re-test region
print("\n=== key block facts ===")
for off in (7184, 7186, 7212, 7216, 7248, 7270, 7372, 7488, 7492, 7582, 9194, 9206, 9210, 9218):
    b = by_off.get(off)
    if b is None:
        print("  @%-6d no block" % off)
        continue
    r = an.get_region_for_block(b)
    print("  @%-6d win=@%d..@%d(%d) last=%s succ=%s preds=%s region=%s@%s" % (
        off, b.instructions[0].offset, b.instructions[-1].offset, len(b.instructions),
        last_info(b), [so(s) for s in (b.successors or [])],
        [so(p) for p in (b.predecessors or [])],
        type(r).__name__ if r else None, so(getattr(r, 'condition_block', None) or getattr(r, 'entry_block', None) or getattr(r, 'header_block', None)) if r else None))

# disassemble original lines around the region for ground truth
print("\n=== dis around 7160..7280 (line map) ===")
ln = {}
for a, b, off in target.co_lines():
    ln[off] = b
for i in dis.get_instructions(target):
    if 7160 <= i.offset <= 7280:
        print("  @%-6d %-30s %-20s line=%s" % (i.offset, i.opname, i.argrepr, ln.get(i.offset)))
