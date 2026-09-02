import sys, types
sys.path.insert(0, '.')
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
import ast as ast_mod

pyc = load_pyc_file_v2('site-packages/IQCommon/logger/handlers.pyc')
code_obj = pyc.code.get()
pyc_code = code_obj.to_python_code()

for const in pyc_code.co_consts:
    if isinstance(const, types.CodeType) and 'TWHThreadRotating' in const.co_name:
        for inner in const.co_consts:
            if isinstance(inner, types.CodeType) and inner.co_name == '_target':
                cfg = build_cfg(inner)
                analyzer = RegionAnalyzer(cfg)
                regions = analyzer.analyze()
                
                gen = RegionASTGenerator(cfg, regions, inner)
                result = gen.generate()
                
                print(f'Type of result: {type(result)}')
                if isinstance(result, dict):
                    for k, v in result.items():
                        print(f'  Key: {k}, Type: {type(v)}')
                        if isinstance(v, ast_mod.AST):
                            print(f'  AST: {ast_mod.dump(v)}')
                        elif isinstance(v, list):
                            for i, item in enumerate(v):
                                if isinstance(item, ast_mod.AST):
                                    print(f'  [{i}]: {ast_mod.unparse(item)}')
                                else:
                                    print(f'  [{i}]: {item}')
                        else:
                            print(f'  Value: {v}')
