import io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
d = io.open(REPO + r'/site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc','rb').read()
code = marshal.loads(d[16:])
def walk(c,o):
    o.append(c)
    for k in c.co_consts:
        if isinstance(k,types.CodeType): walk(k,o)
    return o
target=[x for x in walk(code,[]) if x.co_name=='get_etf_stock_info'][0]
from core.cfg import build_cfg
from core.cfg import region_ast_generator as G
gen_cls=G.RegionASTGenerator
def off(b): return getattr(b,'start_offset',None)
import linecache
for nm in ('_if_generate_then_branch','_if_generate_normal','_generate_if'):
    fn=getattr(gen_cls,nm)
    def mk(nm,fn):
        def w(*a,**k):
            reg=a[1] if len(a)>1 else None
            e=off(getattr(reg,'entry',None))
            tb=off(getattr(reg,'then_blocks',[None])[0]) if getattr(reg,'then_blocks',None) else None
            r=fn(*a,**k)
            if e==0:
                print('### %s entry=0 then_block=%s' % (nm,tb))
                print('    RET', repr(r)[:700])
            return r
        return w
    setattr(gen_cls,nm,mk(nm,fn))
cfg=build_cfg(target)
gen=gen_cls(cfg, top_level_code=None)
res=gen.generate()
