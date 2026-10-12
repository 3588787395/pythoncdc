"""Probe (INERT, monkey-patch only, no file edit): dump how the analyzer regions the
_sync_worker compound while. Confirms the r65a premise against the CURRENT landed bytes."""
import marshal, os, sys, types
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
sys.path.insert(0, REPO)
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, BoolOpRegion, IfRegion

PYC = os.path.join(REPO, 'site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc')
CO = type(compile('', '', 'exec'))
def gather(c, acc):
    acc.append(c)
    for x in c.co_consts:
        if isinstance(x, CO): gather(x, acc)
top = marshal.loads(open(PYC,'rb').read()[16:])
acc = []; gather(top, acc)
sync = [c for c in acc if c.co_name=='_sync_worker'][0]
cfg = build_cfg(sync)
an = RegionAnalyzer(cfg)
regions = an.analyze()
print("total regions", len(regions))
for r in regions:
    if not isinstance(r, LoopRegion):
        continue
    cb = r.condition_block
    hb = r.header_block
    print("LOOP cond=%s hdr=%s entry=%s back=%s nbody=%s" % (
        getattr(cb,'start_offset',None), getattr(hb,'start_offset',None),
        getattr(r.entry,'start_offset',None) if r.entry else None,
        getattr(getattr(r,'back_edge_block',None),'start_offset',None),
        len(r.body_blocks or [])))
    print("   body_offsets=", sorted(b.start_offset for b in (r.body_blocks or [])))
    if cb is not None:
        li = cb.get_last_instruction()
        print("   cond last=%s -> %s" % (li.opname, li.argval if li.argval is not None else None))
# BoolOp regions
print("=== BoolOpRegions")
for r in regions:
    if isinstance(r, BoolOpRegion):
        print("BOOLREG entry=%s op_chain=%s" % (getattr(r.entry,'start_offset',None),
            [(b.start_offset,op) for b,op in r.op_chain]))
print("=== block_to_region for A(362) B(520) C1(542) C2(698) body(704)")
for off in (232,362,520,542,698,704,874,1032,1054,1208):
    b = cfg.get_block_by_offset(off)
    r = an.block_to_region.get(b) if b else None
    print(" off=%s region=%s%s" % (off, type(r).__name__ if r else None,
        (" cond=%s" % getattr(r.condition_block,'start_offset',None)) if isinstance(r,LoopRegion) else ""))
