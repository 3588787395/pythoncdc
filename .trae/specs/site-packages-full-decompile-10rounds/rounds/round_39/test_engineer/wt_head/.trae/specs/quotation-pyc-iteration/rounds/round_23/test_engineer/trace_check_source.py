"""R23-N4: 跟踪 AST → source 转换"""
import sys
import types

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

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

    print("=== AST dict 结构 ===")
    print(f"  type: {ast_dict.get('type')}")
    if ast_dict.get('type') == 'FunctionDef':
        body = ast_dict.get('body', [])
        for i, node in enumerate(body):
            if isinstance(node, dict) and node.get('type') == 'If':
                # 走到最深的 orelse
                cur = node
                depth = 0
                while cur:
                    orelse = cur.get('orelse', [])
                    print(f"  depth {depth}: If, orelse has {len(orelse)} items, types: {[o.get('type') if isinstance(o, dict) else type(o).__name__ for o in orelse]}")
                    if orelse and isinstance(orelse[0], dict) and orelse[0].get('type') == 'If':
                        cur = orelse[0]
                        depth += 1
                    else:
                        # 这是最后的 else
                        print(f"  >>> 最深 else 内容 <<<")
                        for j, oe in enumerate(orelse):
                            print(f"    orelse[{j}]: {oe.get('type') if isinstance(oe, dict) else type(oe).__name__}")
                            if isinstance(oe, dict) and oe.get('type') == 'If':
                                print(f"      test: {oe.get('test', {}).get('type')}")
                                print(f"      body: {[b.get('type') for b in oe.get('body', [])]}")
                                print(f"      orelse: {[o.get('type') for o in oe.get('orelse', [])]}")
                        break

    # 转换为 py_ast
    print("\n=== 转换为 py_ast ===")
    converter = CFGASTConverter()
    py_ast = converter.convert(ast_dict)

    # 查看 py_ast 结构
    import ast
    print(f"py_ast type: {type(py_ast).__name__}")
    if isinstance(py_ast, ast.FunctionDef):
        for i, stmt in enumerate(py_ast.body):
            print(f"  body[{i}]: {type(stmt).__name__}")
            if isinstance(stmt, ast.If):
                # 走到最深的 orelse
                cur = stmt
                depth = 0
                while cur:
                    orelse = cur.orelse
                    print(f"  depth {depth}: If, orelse has {len(orelse)} items, types: {[type(o).__name__ for o in orelse]}")
                    if orelse and isinstance(orelse[0], ast.If):
                        cur = orelse[0]
                        depth += 1
                    else:
                        print(f"  >>> 最深 else 内容 <<<")
                        for j, oe in enumerate(orelse):
                            print(f"    orelse[{j}]: {type(oe).__name__}")
                            if isinstance(oe, ast.If):
                                print(f"      test: {type(oe.test).__name__}")
                                print(f"      body: {[type(b).__name__ for b in oe.body]}")
                                print(f"      orelse: {[type(o).__name__ for o in oe.orelse]}")
                        break

    # 生成源代码
    print("\n=== 生成源代码 ===")
    code_gen = CFGCodeGenerator()
    source = code_gen.generate(py_ast)
    print(source)


if __name__ == '__main__':
    main()
