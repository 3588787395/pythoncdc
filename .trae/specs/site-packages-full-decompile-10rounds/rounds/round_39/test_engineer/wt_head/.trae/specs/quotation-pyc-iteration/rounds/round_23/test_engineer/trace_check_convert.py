"""R23-N4: 跟踪 CFGASTConverter 对嵌套 If 的处理"""
import sys
import types

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter

PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
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
    co = pyc_codes['check_index_code']

    cfg = build_cfg(co)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    ast_dict = gen.generate()

    # 创建 converter 并 monkey-patch convert_if
    converter = CFGASTConverter()
    original_convert = converter.convert

    call_depth = [0]
    def traced_convert(node):
        call_depth[0] += 1
        indent = '  ' * call_depth[0]
        if isinstance(node, dict):
            print(f"{indent}convert: dict type={node.get('type')}, _is_elif={node.get('_is_elif')}, has_orelse={'orelse' in node}")
            if node.get('type') == 'If':
                orelse = node.get('orelse', [])
                print(f"{indent}  orelse: {len(orelse)} items, types: {[o.get('type') if isinstance(o, dict) else type(o).__name__ for o in orelse]}")
        result = original_convert(node)
        if result is None:
            print(f"{indent}  -> RESULT: None")
        elif isinstance(result, list):
            print(f"{indent}  -> RESULT: list of {len(result)}")
        else:
            print(f"{indent}  -> RESULT: {type(result).__name__}")
        call_depth[0] -= 1
        return result
    converter.convert = traced_convert

    py_ast = converter.convert(ast_dict)

    # 生成源代码
    from core.cfg.code_generator import CFGCodeGenerator
    code_gen = CFGCodeGenerator()
    source = code_gen.generate(py_ast)
    print("\n=== SOURCE ===")
    print(source)


if __name__ == '__main__':
    main()
