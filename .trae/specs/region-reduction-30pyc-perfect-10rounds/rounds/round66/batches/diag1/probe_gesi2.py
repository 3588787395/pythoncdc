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
cands=[n for n in dir(gen_cls) if 'if' in n.lower()]
print('IF METHODS:', cands)
def off(b): return getattr(b,'start_offset',None)
for nm in cands:
    fn=getattr(gen_cls,nm)
    if not callable(fn): continue
    def mk(nm,fn):
        def w(*a,**k):
            reg=a[1] if len(a)>1 else None
            e=off(getattr(reg,'entry',None))
            r=fn(*a,**k)
            if e in (0,None):
                txt=repr(r)
                print('CALL %-45s entry=%s len=%s body_has_in_stock=%s' % (nm,e,(len(r) if hasattr(r,'__len__') else '?'),'in_stock' in txt[:400]))
            return r
        return w
    setattr(gen_cls,nm,mk(nm,fn))
cfg=build_cfg(target)
gen=gen_cls(cfg, top_level_code=None)
res=gen.generate()
