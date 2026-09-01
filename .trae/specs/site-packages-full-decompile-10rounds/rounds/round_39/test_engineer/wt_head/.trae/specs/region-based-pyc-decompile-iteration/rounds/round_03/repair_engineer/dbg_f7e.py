import sys, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
import core.cfg.region_ast_generator as rag
from core.cfg import decompile

for name, fn in [('_build_ternary_value_expr', rag.RegionASTGenerator._build_ternary_value_expr),
                 ('_try_build_ternary_store_assign', rag.RegionASTGenerator._try_build_ternary_store_assign),
                 ('_build_ternary_no_target_consumer_stmt', rag.RegionASTGenerator._build_ternary_no_target_consumer_stmt)]:
    pass

def wrap(name):
    orig = getattr(rag.RegionASTGenerator, name)
    def w(self, *a, **k):
        r = orig(self, *a, **k)
        print(f"  [dbg] {name}({a[1] if len(a)>1 else ''}) -> {r if name!='_build_ternary_value_expr' else ''}")
        return r
    setattr(rag.RegionASTGenerator, name, w)

orig_val = rag.RegionASTGenerator._build_ternary_value_expr
def wrapped_val(self, block):
    r = orig_val(self, block)
    print(f"  [dbg] _build_ternary_value_expr(off={block.start_offset}) -> {r}")
    return r
rag.RegionASTGenerator._build_ternary_value_expr = wrapped_val

for n in ('_try_build_ternary_store_assign','_build_ternary_no_target_consumer_stmt'):
    o = getattr(rag.RegionASTGenerator, n)
    def mk(o, n):
        def w(self, region, te):
            r = o(self, region, te)
            print(f"  [dbg] {n}(te={te.get('type') if isinstance(te,dict) else te}) -> {r}")
            return r
        return w
    setattr(rag.RegionASTGenerator, n, mk(o, n))

src = '''class A:
    def __init__(self, d, k, v=None):
        self.d = {}
        self.d[k] = v if v is not None else default()
        self.register_event()
'''
print(decompile(src, '<f7e>'))
