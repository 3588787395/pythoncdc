import io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main'); sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    d=io.open(p,'rb').read()
    return marshal.loads(d[16:])
def walk(c,o):
    o.append(c)
    for k in c.co_consts:
        if isinstance(k,types.CodeType): walk(k,o)
    return o
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator as GC
import dis
NOISE={'RESUME','NOP','CACHE','PUSH_NULL','POP_TOP'}
def offs(bs): return [getattr(b,'start_offset',None) for b in (bs or [])]
def body(bs):
    out=[]
    for b in (bs or []):
        out.append('[%s]'%','.join(i.opname for i in b.instructions if i.opname not in ('CACHE',)))
    return ' '.join(out)
orig=GC._merge_block_is_then_exclusive
def w(self, region):
    r=orig(self, region)
    print('W15C entry=%s -> %s' % (getattr(region.entry,'start_offset',None), r))
    print('   then=%s %s'%(offs(region.then_blocks), body(region.then_blocks)))
    print('   else=%s %s'%(offs(region.else_blocks), body(region.else_blocks)))
    print('   cond=%s %s'%(offs([region.condition_block]), body([region.condition_block])))
    print('   cc=%s %s'%(offs(getattr(region,'chained_compare_blocks',None)), body(getattr(region,'chained_compare_blocks',None))))
    print('   merge=%s %s   rt=%s  children=%d blocks=%s'%(getattr(region.merge_block,'start_offset',None),
          body([region.merge_block]) if region.merge_block else '', region.region_type.name,
          len(region.children or []), offs(region.blocks)))
    return r
GC._merge_block_is_then_exclusive=w
P=r'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc'
top=load(P)
for c in walk(top,[]):
    if c.co_name!='tick_worker_thread': continue
    cfg=build_cfg(c); g=GC(cfg, top_level_code=None); g.generate()
