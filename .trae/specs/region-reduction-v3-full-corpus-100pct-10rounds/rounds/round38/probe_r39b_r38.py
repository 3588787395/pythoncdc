"""Which conjunct of the landed [R39-B] arm-tail-continue rule blocks _process_cancel_order?

Read-only: builds the CFG + regions for trade_live_broker._process_cancel_order and evaluates the rule
(region_ast_generator.py:27800-27852) against the two arms the measured loss sits in:
  outer else arm   tail block @1930..@1994  -> T @1998 (JUMP_BACKWARD -> @44)  missing in the product
  inner else arm   tail block @1746..@1820  -> T @1824 (JUMP_BACKWARD -> @44)  present via [R21-35a] only
Nothing is written; no generator is instantiated, so no product can be perturbed.

usage: python -X utf8 probe_r39b_r38.py
"""
import marshal
import os
import sys

REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
sys.path.insert(0, REPO)
PYC = os.path.join(REPO, "site-packages", "IQEngine", "plugins",
                   "plugin_system_trade", "trade_live_broker.pyc")
UNIT = "_process_cancel_order"

from core.cfg import build_cfg                                              # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion           # noqa: E402

CO = type(compile("", "", "exec"))


def gather(c, acc):
    acc.append(c)
    for cst in c.co_consts:
        if isinstance(cst, CO):
            gather(cst, acc)


def blk_at(cfg, off):
    for b in cfg.blocks.values() if isinstance(cfg.blocks, dict) else cfg.blocks:
        if b.instructions and b.instructions[0].offset == off:
            return b
    return None


code = marshal.loads(open(PYC, "rb").read()[16:])
acc = []
gather(code, acc)
target = max([c for c in acc if c.co_name == UNIT], key=lambda c: len(c.co_code))
cfg = build_cfg(target)
an = RegionAnalyzer(cfg)
regions = an.analyze()
blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
print("unit lines=%d blocks=%d regions=%d" % (len(target.co_code), len(blocks), len(regions)))
loops = [r for r in regions if isinstance(r, LoopRegion)]
for lp in loops:
    hb = lp.header_block
    print("LOOP header=%s back_edge=%s cond=%s n_back_edges=%s body=%d" % (
        hb.instructions[0].offset if hb and hb.instructions else None,
        lp.back_edge_block.instructions[0].offset if getattr(lp, 'back_edge_block', None) and lp.back_edge_block.instructions else None,
        lp.condition_block.instructions[0].offset if getattr(lp, 'condition_block', None) and lp.condition_block.instructions else None,
        len(getattr(lp, 'back_edge_blocks', None) or []), len(lp.body_blocks or [])))
    if hb and hb.instructions:
        print("   header first instrs:", [(i.opname, i.offset) for i in hb.instructions[:3]])

NOISE = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG')


def report(tail_off, t_off):
    print("\n=== rule evaluation for tail @%d -> T @%d" % (tail_off, t_off))
    L = blk_at(cfg, tail_off)
    T = blk_at(cfg, t_off)
    if L is None or T is None:
        print("   block missing (tail found=%s T found=%s)" % (L is not None, T is not None))
        return
    lp = [r for r in loops if T in (r.body_blocks or []) or T is r.header_block
          or T in getattr(r, 'blocks', ()) or L in (r.body_blocks or [])]
    lp = lp[0] if lp else (loops[-1] if loops else None)
    hdr = getattr(lp, 'header_block', None)
    print("   loop header=%s" % (hdr.instructions[0].offset if hdr and hdr.instructions else None))
    succs = [s for s in (list(L.successors) or [])
             if s.start_offset > L.start_offset
             and not (list(getattr(s, 'instructions', None) or [])
                      and s.get_first_instruction().opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START'))]
    print("   C1 stmts non-empty (arm emitted): assumed")
    print("   C2 L in generated_blocks: (runtime state, unknown here)  L last instr=%s" %
          (L.get_last_instruction().opname,))
    print("   C3 len(forward succs of L)==1 -> %s %s" % (len(succs),
          [(s.instructions[0].offset if s.instructions else None) for s in succs]))
    Tins = list(getattr(T, 'instructions', None) or [])
    print("   C4 len(T.instructions)==1 -> %d %s" % (len(Tins), [(i.opname, i.offset) for i in Tins]))
    tp = list(getattr(T, 'predecessors', None) or [])
    print("   C5 T preds==[L] -> %s %s" % (len(tp),
          [(p.instructions[0].offset if p.instructions else None) for p in tp]))
    print("   C6 T not in region.blocks -> T region=%s" % (
        type(an.get_region_for_block(T)).__name__ if an.get_region_for_block(T) else None))
    print("   C7 T not a back_edge of the loop -> in back_edge_blocks=%s is back_edge_block=%s" % (
        T in (getattr(lp, 'back_edge_blocks', None) or []), T is getattr(lp, 'back_edge_block', None)))
    tl = T.get_last_instruction()
    tgt = cfg.get_block_by_offset(tl.argval) if tl is not None and tl.argval is not None else None
    print("   C8 T last op=%s argval=%s -> block @%s ; is header? %s" % (
        tl.opname if tl else None, tl.argval if tl else None,
        tgt.instructions[0].offset if tgt and tgt.instructions else None, tgt is hdr))
    ll = L.get_last_instruction()
    print("   C9 L last instr has no JUMP -> %s" % ('JUMP' not in (ll.opname if ll else 'JUMP')))
    print("   role(T)=%s role(L)=%s" % (an.get_block_role(T), an.get_block_role(L)))


report(1930, 1998)
report(1746, 1824)
