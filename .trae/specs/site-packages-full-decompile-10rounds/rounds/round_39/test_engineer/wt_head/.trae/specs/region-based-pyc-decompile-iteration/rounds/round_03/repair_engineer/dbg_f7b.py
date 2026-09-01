import sys, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TernaryRegion
from core.cfg.region_ast_generator import RegionASTGenerator

def get_regions(src, name):
    code = compile(src, '<dbg>', 'exec')
    def find(co, n):
        if co.co_name == n: return co
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                r = find(c, n)
                if r: return r
    init = find(code, name)
    cfg = build_cfg(init)
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()
    return analyzer, regions

def attrs(r):
    out = {}
    for a in ('value_target','merge_context','container_type'):
        if hasattr(r,a): out[a]=getattr(r,a)
    return out

def dump(analyzer, regions, label):
    print(f"===== {label} =====")
    for r in regions:
        if isinstance(r, TernaryRegion):
            print("TernaryRegion:", attrs(r))
            mb = r.merge_block
            print("  merge_block instrs:")
            for i in mb.instructions:
                if i.opname not in ('RESUME','NOP','CACHE','PRECALL'):
                    print(f"    {i.offset}: {i.opname} {i.argval if i.argval is not None else ''}")
            cb = r.condition_block
            print("  condition_block instrs:")
            for i in cb.instructions:
                if i.opname not in ('RESUME','NOP','CACHE','PRECALL'):
                    print(f"    {i.offset}: {i.opname} {i.argval if i.argval is not None else ''}")

src_f7 = '''class A:
    def __init__(self, total_cash, positions, processed_trade=None):
        self._total_cash = total_cash
        self._processed_trade = processed_trade if processed_trade is not None else set()
        self._transaction_cost = 0
        self.register_event()
'''
src_case2 = '''def f(self, p, c):
    self.x = p if c else 0
    self.y = 1
    return self.y
'''
a1,r1 = get_regions(src_f7,'__init__')
dump(a1,r1,'F7 __init__')
a2,r2 = get_regions(src_case2,'f')
dump(a2,r2,'CASE2 f')

# Now instrument _generate_ternary
import core.cfg.region_ast_generator as rag
orig = rag.RegionASTGenerator._generate_ternary
def wrapped(self, region, *args, **kw):
    res = orig(self, region, *args, **kw)
    if isinstance(region, TernaryRegion):
        print("GEN ternary ->", res)
    return res
rag.RegionASTGenerator._generate_ternary = wrapped

print("=== generate F7 ===")
from core.cfg import decompile
print(decompile(src_f7,'<f7>'))
print("=== generate CASE2 ===")
print(decompile(src_case2,'<c2>'))
