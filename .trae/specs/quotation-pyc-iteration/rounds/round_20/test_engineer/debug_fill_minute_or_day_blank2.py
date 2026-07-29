"""R20 测试工程师：dump fill_minute_or_day_blank 的所有CFG块和区域结构"""
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

        cfg = CFGBuilder().build(co)
        blocks = cfg.blocks
        for k in sorted(blocks.keys()):
            b = blocks[k]
            print(f"  block {k} (start {b.start_offset}): succs={[s.id for s in b.successors]} preds={[p.id for p in b.predecessors]}")

        # 尝试区域分析
        print()
        try:
            from core.cfg.region_analyzer import RegionAnalyzer
            analyzer = RegionAnalyzer()
            result = analyzer.analyze(cfg)
            print(f"region_analyzer.analyze result type: {type(result).__name__}")
            if hasattr(result, '__len__'):
                print(f"len: {len(result)}")
            print(f"result: {result}")
        except Exception as e:
            print(f"region_analyzer ERROR: {e}")
            traceback.print_exc()

        # 尝试AST生成
        print()
        try:
            from core.cfg.region_ast_generator import RegionASTGenerator
            gen = RegionASTGenerator()
            ast = gen.generate(cfg, co)
            print(f"AST generator type: {type(ast).__name__}")
            print(f"AST: {ast}")
        except Exception as e:
            print(f"AST generator ERROR: {e}")
            traceback.print_exc()

    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    main()
