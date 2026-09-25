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
gen_cls = G.RegionASTGenerator
names=[n for n in dir(gen_cls) if 'if' in n.lower() and 'block' in n.lower()]
print('if/block methods:', names)
logged=[]
def wrap(nm):
    orig=getattr(gen_cls,nm)
    def w(*a,**k):
        reg=a[1] if len(a)>1 else None
        e=getattr(getattr(reg,'entry',None),'start_offset',None)
        r=orig(*a,**k)
        try:
            cnt=len(r)
        except Exception:
            cnt=-1
        logged.append((nm,e,cnt,repr(r)[:220]))
        return r
    for attr in dir(gen_cls):
        pass
    return w
for nm in names:
    try: setattr(gen_cls,nm,wrap(nm))
    except Exception as ex: print('skip',nm,ex)
cfg=build_cfg(target)
gen=gen_cls(cfg, top_level_code=None)
res=gen.generate()
for nm,e,cnt,r in logged:
    if e in (0,10,12,56,None) :
        print('%-40s entry=%s n=%s %s'%(nm,e,cnt,r))
