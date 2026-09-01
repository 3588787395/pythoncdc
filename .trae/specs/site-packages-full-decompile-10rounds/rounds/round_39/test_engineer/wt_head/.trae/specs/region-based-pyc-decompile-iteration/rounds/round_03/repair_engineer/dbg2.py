import sys
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
import dis, types
from core.cfg import decompile
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

src='''
class C:
    X = X
    def m(self):
        return 1
'''
co = compile(src,'<s>','exec')
# find class code object
cls_co = [c for c in co.co_consts if isinstance(c, types.CodeType) and c.co_name=='C'][0]
builder=CFGBuilder(); cfg=builder.build(cls_co); an=RegionAnalyzer(cfg); an.analyze()
gen=RegionASTGenerator(cfg, an)
res=gen.generate()
print("CLASS BODY generate() result type:", type(res))
if isinstance(res, dict):
    print("body stmts:", res.get('body'))
elif isinstance(res, list):
    print("list:", res)
