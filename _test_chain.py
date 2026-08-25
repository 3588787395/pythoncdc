import sys, types, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator

pyc_path = 'site-packages/IQCommon/arg_checker.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

for c in code.co_consts:
    if isinstance(c, types.CodeType) and c.co_name == 'ArgumentChecker':
        for c2 in c.co_consts:
            if isinstance(c2, types.CodeType) and c2.co_name == '_is_valid_quarter':
                builder = CFGBuilder()
                cfg = builder.build(c2)
                ra = RegionAnalyzer(cfg, c2)
                ra.analyze()
                gen = RegionASTGenerator(cfg, c2, ra)
                
                for r in ra.regions:
                    if isinstance(r, BoolOpRegion) and r.entry.start_offset == 166:
                        expr = gen._build_boolop_expression(r)
                        if expr:
                            t = expr.get('type')
                            if t == 'Compare':
                                print('Compare:', expr.get('ops'), len(expr.get('comparators',[])))
                            elif t == 'BoolOp':
                                print('BoolOp:', expr.get('op'), len(expr.get('values',[])))
                                for v in expr.get('values',[]):
                                    print('  val:', v.get('type'), v.get('ops') if v.get('type')=='Compare' else '')
                            else:
                                print('Type:', t)
                        else:
                            print('None')
                
                break
        break
