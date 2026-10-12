"""R21-44 MEASURE harness (monkey-patch, NO file edit): install the proposed analyzer
nested or-head/and-tail detector and regenerate broker + judge + per-unit diff.

Proves end-to-end whether the analyzer-side compound-while rebuild FLIPS _sync_worker
before committing to a byte-level candidate. inert probe -> measure -> restore.
"""
import marshal, os, sys, subprocess, importlib
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
MIRROR = r"D:/Temp/r71"
sys.path.insert(0, MIRROR)          # mirror core/ (landed bytes)
from core.cfg import region_analyzer as RA
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, BoolOpRegion
from core.cfg.region_analyzer import FORWARD_CONDITIONAL_JUMP_OPS

MODE = sys.argv[1] if len(sys.argv) > 1 else "analyzer"   # analyzer | both | none

def _r71_resolve(self, block):
    seen = 0
    while block is not None and seen < 4:
        eff = [i for i in block.instructions if i.opname not in ('RESUME','NOP','CACHE','EXTENDED_ARG','PUSH_NULL')]
        if len(eff) == 1 and eff[0].opname in ('JUMP_FORWARD','JUMP_BACKWARD') and eff[0].argval is not None:
            block = self.cfg.get_block_by_offset(eff[0].argval); seen += 1
        else:
            return block
    return block

def _r71_detect_or_and(self, cond_block, loop):
    if cond_block is None or loop.header_block is None:
        return None
    sem = set(loop.body_blocks or [])
    sem.add(loop.header_block)
    if loop.entry is not None: sem.add(loop.entry)
    if loop.condition_block is not None: sem.add(loop.condition_block)
    last = cond_block.get_last_instruction()
    if last is None or last.argval is None or 'TRUE' not in (last.opname or '') \
            or last.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
        return None
    true_exit = _r71_resolve(self, self.cfg.get_block_by_offset(last.argval))
    if true_exit is None or true_exit not in sem:
        return None
    or_members = []
    cur = cond_block
    false_exit = None
    while True:
        cl = cur.get_last_instruction()
        if cl is None or cl.argval is None or cl.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
            return None
        tgt = _r71_resolve(self, self.cfg.get_block_by_offset(cl.argval))
        succs = list(cur.conditional_successors)
        if len(succs) != 2:
            return None
        ft = next((s for s in succs if s.start_offset != cl.argval), None)
        if ft is None:
            return None
        if 'TRUE' in cl.opname and tgt is true_exit:
            or_members.append((cur, 'or'))
            if ft in sem:
                return None
            cur = ft
            continue
        if 'FALSE' in cl.opname and tgt is not true_exit:
            false_exit = tgt
            break
        return None
    if len(or_members) < 2 or false_exit is None:
        return None
    and_members = []
    while True:
        cl = cur.get_last_instruction()
        if cl is None or cl.argval is None or cl.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
            return None
        tgt = _r71_resolve(self, self.cfg.get_block_by_offset(cl.argval))
        succs = list(cur.conditional_successors)
        if len(succs) != 2:
            return None
        ft = next((s for s in succs if s.start_offset != cl.argval), None)
        if ft is None or tgt is not false_exit:
            return None
        and_members.append((cur, 'and'))
        if _r71_resolve(self, ft) is true_exit:
            break
        if ft in sem:
            return None
        cur = ft
    if len(and_members) < 2:
        return None
    return or_members + and_members

_orig = RegionAnalyzer._detect_while_condition_boolop_chain
if MODE in ("analyzer","both"):
    RegionAnalyzer._r71_detect_or_and = _r71_detect_or_and
    def _patched(self, cond_block, loop):
        r = _orig(self, cond_block, loop)
        chain = self._r71_detect_or_and(cond_block, loop)
        print("[R71] called cond=%s hdr=%s orig=%s r71=%s" % (
            getattr(cond_block,'start_offset',None),
            getattr(getattr(loop,'header_block',None),'start_offset',None),
            (len(r) if r else None), ([(b.start_offset,o) for b,o in chain] if chain else None)))
        if r and len(r) >= 2:
            return r
        if chain and len(chain) >= 2:
            return chain
        return r
    RegionAnalyzer._detect_while_condition_boolop_chain = _patched
    _ocreate = RegionAnalyzer._create_boolop_region_from_chain
    def _ctrace(self, chain, claimed):
        res = _ocreate(self, chain, claimed)
        if chain and len(chain) >= 2 and chain[0][0].start_offset == 232:
            print("[R71] _create chain=%s -> %s" % ([(b.start_offset,o) for b,o in chain],
                  'REGION entry@%s blocks=%s' % (getattr(res.entry,'start_offset',None),
                    sorted(x.start_offset for x in res.blocks)) if res else 'None(REJECTED)'))
        return res
    RegionAnalyzer._create_boolop_region_from_chain = _ctrace

import pycdc  # noqa
PYC = os.path.join(REPO, 'site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc')
out = os.path.join(MIRROR, 'prod', 'broker_%s.py' % MODE)
# generate via the in-process pipeline
sys.argv = ['pycdc.py','--region','-o',out, PYC]
try:
    pycdc.main()
except SystemExit:
    pass
print("WROTE", out, os.path.exists(out))
