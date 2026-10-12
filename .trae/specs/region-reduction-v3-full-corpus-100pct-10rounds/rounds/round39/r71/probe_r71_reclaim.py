import marshal,os,sys,traceback
sys.path.insert(0,'.')
import core.cfg.region_analyzer as RA
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, BoolOpRegion
created=[]
_oc=RA.RegionAnalyzer._create_boolop_region_from_chain
def ctrace(self,chain,claimed):
    r=_oc(self,chain,claimed)
    if r and chain and chain[0][0].start_offset==232:
        created.append(r); print('[create] id=%d blocks=%s'%(id(r),sorted(b.start_offset for b in r.blocks)))
    return r
RA.RegionAnalyzer._create_boolop_region_from_chain=ctrace
_orig=RA.RegionAnalyzer._detect_while_condition_boolop_chain
def patched(self,cb,loop):
    res=_orig(self,cb,loop)
    if res and len(res)>=2: return res
    if getattr(cb,'start_offset',None)==232 and getattr(getattr(loop,'header_block',None),'start_offset',None)==704:
        b=[self.cfg.get_block_by_offset(o) for o in (232,364,522,544)]
        return [(b[0],'or'),(b[1],'or'),(b[2],'and'),(b[3],'and')]
    return res
RA.RegionAnalyzer._detect_while_condition_boolop_chain=patched
# hook list.remove on self.regions to catch removal of my region id
from core.cfg import build_cfg
CO=type(compile('','','exec'))
def gather(c,acc):
    acc.append(c)
    for x in c.co_consts:
        if isinstance(x,CO): gather(x,acc)
pyc='D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc'
acc=[]; gather(marshal.loads(open(pyc,'rb').read()[16:]),acc)
sync=[c for c in acc if c.co_name=='_sync_worker'][0]
cfg=build_cfg(sync); an=RegionAnalyzer(cfg)
# patch block_to_region set to detect when 232 reassigned
_origbtr = an.block_to_region
class Watch(dict):
    def __setitem__(self,k,v):
        if created and getattr(k,'start_offset',None)==232 and v is not created[-1]:
            print('[reclaim] block232 -> %s id=%d'%(type(v).__name__, id(v)))
            traceback.print_stack(limit=6)
        super().__setitem__(k,v)
an.block_to_region=Watch(_origbtr)
regions=an.analyze()
my=created[-1]
print('final: my in regions?', any(r is my for r in regions), 'btr232=',type(an.block_to_region.get(cfg.get_block_by_offset(232))).__name__)
