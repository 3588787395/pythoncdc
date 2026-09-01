"""R20 测试工程师：dump fill_minute_or_day_blank 的区域分析结果"""
import sys
import types
import traceback

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    if not module:
        return {}
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    name = 'fill_minute_or_day_blank'
    co = pyc_codes[name]
    print(f"=== {name} ===")

    try:
        from core.cfg.cfg_builder import CFGBuilder
        from core.cfg.region_analyzer import RegionAnalyzer
        from core.cfg.region_ast_generator import RegionASTGenerator

        cfg = CFGBuilder().build(co)

        # RegionAnalyzer接受cfg
        analyzer = RegionAnalyzer(cfg)
        regions = analyzer.analyze()
        print(f"region_analyzer.analyze() result type: {type(regions).__name__}")
        if hasattr(regions, '__len__'):
            print(f"len: {len(regions)}")
        if hasattr(regions, 'items'):
            for k, v in list(regions.items())[:20]:
                print(f"  region {k}: {type(v).__name__} {v}")
        elif hasattr(regions, '__iter__'):
            for r in list(regions)[:20]:
                print(f"  region: {type(r).__name__} {r}")

        print()
        # RegionASTGenerator也接受cfg
        gen = RegionASTGenerator(cfg, co)
        ast = gen.generate()
        print(f"AST type: {type(ast).__name__}")
        print(f"AST: {ast}")

    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    main()
