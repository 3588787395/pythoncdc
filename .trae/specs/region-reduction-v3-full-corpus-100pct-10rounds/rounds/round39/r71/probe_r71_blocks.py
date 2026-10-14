import marshal, os, sys
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
sys.path.insert(0, REPO)
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion
PYC = os.path.join(REPO, 'site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc')
CO=type(compile('','','exec'))
def gather(c, acc):
    acc.append(c)
    for x in c.co_consts:
        if isinstance(x,CO): gather(x, acc)
top = marshal.loads(open(PYC,'rb').read()[16:])
acc=[]; gather(top,acc)
sync=[c for c in acc if c.co_name=='_sync_worker'][0]
cfg=build_cfg(sync)
an=RegionAnalyzer(cfg); an.analyze()
print("=== block_to_region for operand blocks")
for off in (232,364,522,544,700,702,704,876,1034,1056,1212):
    b=cfg.get_block_by_offset(off)
    r=an.block_to_region.get(b)
    cb=getattr(r,'condition_block',None)
    print(" blk@%s owner=%s cond=%s hdr=%s"%(off, type(r).__name__ if r else None,
        getattr(cb,'start_offset',None) if r is not None and isinstance(r,LoopRegion) else '-',
        getattr(getattr(r,'header_block',None),'start_offset',None) if isinstance(r,LoopRegion) else '-'))
for off in (232,364,522,544,700,702,704,876,1034,1056,1212,1214):
    b=cfg.get_block_by_offset(off)
    if b is None:
        print("off",off,"NO BLOCK"); continue
    li=b.get_last_instruction()
    fi=b.instructions[0] if b.instructions else None
    cs=[s.start_offset for s in b.conditional_successors]
    print("blk@%s first=%s last=%s->%s cond_succ=%s nsucc=%d"%(
        off, fi.opname if fi else '?', li.opname if li else '?',
        li.argval if li else None, cs, len(b.successors)))
