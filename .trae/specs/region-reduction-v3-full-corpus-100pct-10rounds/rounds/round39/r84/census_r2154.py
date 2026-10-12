"""R21-54 population census (BEFORE editing). Pure region-data predicate over IF_ELIF_CHAIN
regions: single-elif chain whose sole elif condition's false-exit lands inside elif_final_else
(and not inside elif_bodies), with merge_block being itself a conditional test block.

Evaluations + fires over the 20 panel files and corpus-wide; no side effects -> inert by construction.
usage: python -X utf8 work/census_r2154.py [--corpus]
"""
import dis, marshal, os, sys
sys.setrecursionlimit(20000)

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
SP = os.path.join(REPO, "site-packages")
SPEC = os.path.join(REPO, ".trae", "specs", "region-reduction-v3-full-corpus-100pct-10rounds")
PANEL = os.path.join(SPEC, "rounds", "round38", "PANEL_20files.txt")

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, RegionType

CO = type(compile("", "", "exec"))


def gather(c, acc):
    stack = [c]
    while stack:
        cur = stack.pop()
        acc.append(cur)
        for x in cur.co_consts:
            if isinstance(x, CO):
                stack.append(x)


def so(b):
    return b.start_offset if b is not None else None


def pop_jump_target(b):
    """the CFG conditional-false-exit of b: last instruction POP_JUMP_*IF_FALSE/IF_TRUE -> target offset.
    Returns target block offset (int) or None."""
    if b is None or not b.instructions:
        return None
    li = b.get_last_instruction()
    if li is None or not isinstance(getattr(li, 'argval', None), int):
        return None
    if li.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE',
                     'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE',
                     'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE'):
        return li.argval
    return None


def cond_true_exit(c, offset_to_block):
    """a conditional-test block's TRUE edge = fall-through successor whose start offset is the
    next block after c that is not the POP_JUMP target and is not an exception/entry-of-handler
    block. Return its offset or None."""
    if c is None or not c.instructions:
        return None
    li = c.get_last_instruction()
    if li is None or not isinstance(getattr(li, 'argval', None), int):
        return None
    is_false_jump = li.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE',
                                  'POP_JUMP_IF_FALSE')
    false_off = li.argval
    succs = sorted((so(s) for s in (c.successors or []) if s is not None and so(s) is not None))
    for off in succs:
        if off == false_off:
            continue
        b = offset_to_block.get(off)
        fi = b.get_first_instruction() if (b is not None and b.instructions) else None
        if fi is not None and fi.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START'):
            continue
        if not is_false_jump and off == false_off:
            continue
        # for a POP_JUMP_IF_FALSE, the true edge is the non-target successor with offset > c
        if off > so(c):
            return off
    return None


def merge_is_test(b):
    if b is None or not b.instructions:
        return False
    li = b.get_last_instruction()
    return li is not None and li.opname in (
        'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE',
        'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE',
        'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE')


def predicate(region, offset_to_block):
    """Return (evaluated_for_chain: bool, fired: bool, note)."""
    if not isinstance(region, IfRegion):
        return False, False, None
    if getattr(region, 'region_type', None) != RegionType.IF_ELIF_CHAIN:
        return False, False, None
    conds = list(region.elif_conditions or [])
    bodies = list(region.elif_bodies or [])
    if len(conds) != 1 or len(bodies) != 1:
        return True, False, "not-single-elif"
    fin = list(region.elif_final_else or [])
    if not fin:
        return True, False, "no-final-else"
    c = conds[0]
    fx_off = pop_jump_target(c)
    if fx_off is None:
        return True, False, "cond-no-pop-jump-exit"
    body_offs = {so(b) for b in (bodies[0] or [])}
    fin_offs = {so(b) for b in fin}
    merge_off = so(region.merge_block)
    if fx_off not in fin_offs:
        return True, False, "false-exit-not-in-final-else"
    if fx_off in body_offs:
        return True, False, "false-exit-in-body"
    if fx_off == merge_off:
        return True, False, "false-exit-is-merge"
    if not merge_is_test(region.merge_block):
        return True, False, "merge-not-test-block"
    # genuine elif: the condition's TRUE edge falls through into its own claimed body.
    # a mis-collected nested body has its true edge NOT in elif_bodies[0].
    te = cond_true_exit(c, offset_to_block)
    if te is None or te in body_offs:
        return True, False, "true-edge-is-body-or-unknown"
    return True, True, "cond@%s fx@%s te@%s merge@%s fin_n=%d" % (so(c), fx_off, te, merge_off, len(fin))


def census_pyc(path, label):
    try:
        code = marshal.loads(open(path, "rb").read()[16:])
    except Exception as e:
        return None, "ERR %s" % e
    acc = []
    gather(code, acc)
    ev = fire = 0
    notes = []
    for c in acc:
        try:
            cfg = build_cfg(c)
            an = RegionAnalyzer(cfg)
            regions = an.analyze()
        except Exception as e:
            continue
        offset_to_block = {b.start_offset: b for b in cfg.blocks.values() if b.instructions}
        for r in regions:
            e_, f_, note = predicate(r, offset_to_block)
            if e_:
                ev += 1
            if f_:
                fire += 1
                notes.append("%s cond=%s" % (label, note))
    return (ev, fire, len(acc)), notes


files = []
if "--corpus" in sys.argv:
    for root, _, fs in os.walk(SP):
        for f in fs:
            if f.endswith(".pyc"):
                files.append(os.path.join(root, f))
else:
    for line in open(PANEL, encoding="utf-8"):
        line = line.strip()
        if line:
            files.append(os.path.join(SP, line.replace("/", os.sep)))

tot_ev = tot_fire = 0
all_notes = []
for p in files:
    lbl = os.path.relpath(p, SP).replace(os.sep, "/")
    res, notes = census_pyc(p, lbl)
    if res is None:
        print("ERR   %-60s %s" % (lbl, notes))
        continue
    ev, fire, nco = res
    tot_ev += ev; tot_fire += fire
    if fire or "--all" in sys.argv:
        print("%-58s co=%-4d chains_eval=%-4d FIRES=%d" % (lbl, nco, ev, fire))
    all_notes.extend(notes)

print("\n=== TOTALS files=%d chains_eval=%d FIRES=%d ===" % (len(files), tot_ev, tot_fire))
for n in all_notes:
    print("  FIRE:", n)
