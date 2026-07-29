"""R23-N4: 调试 get_str_data 的 AST 结构，找 for 循环体重复生成问题"""
import sys
import json
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

PYC = '/workspace/quotation.pyc'


def load_code():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    return code_obj


def find_func(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, type(co)):
            r = find_func(c, name)
            if r:
                return r
    return None


def dump_ast(node, depth=0, max_depth=8):
    """递归打印 AST"""
    if depth > max_depth:
        return
    indent = '  ' * depth
    if isinstance(node, dict):
        t = node.get('type', '?')
        if t == 'For':
            print(f"{indent}For target={node.get('target')} iter={node.get('iter')}")
            print(f"{indent}  body:")
            for s in node.get('body', []):
                dump_ast(s, depth + 2, max_depth)
        elif t == 'Expr':
            v = node.get('value', {})
            print(f"{indent}Expr value_type={v.get('type') if isinstance(v, dict) else type(v).__name__}")
            if isinstance(v, dict):
                dump_ast(v, depth + 2, max_depth)
        elif t == 'Assign':
            print(f"{indent}Assign targets={node.get('targets')}")
            dump_ast(node.get('value'), depth + 2, max_depth)
        elif t == 'Subscript':
            print(f"{indent}Subscript")
            dump_ast(node.get('value'), depth + 2, max_depth)
            dump_ast(node.get('slice'), depth + 2, max_depth)
        elif t == 'Name':
            print(f"{indent}Name id={node.get('id')}")
        elif t == 'Constant':
            print(f"{indent}Constant value={node.get('value')!r}")
        elif t == 'UnaryOp':
            print(f"{indent}UnaryOp op={node.get('op')}")
            dump_ast(node.get('operand'), depth + 2, max_depth)
        elif t == 'BinOp':
            print(f"{indent}BinOp op={node.get('op')}")
            dump_ast(node.get('left'), depth + 2, max_depth)
            dump_ast(node.get('right'), depth + 2, max_depth)
        elif t == 'If':
            print(f"{indent}If")
            print(f"{indent}  test:")
            dump_ast(node.get('test'), depth + 3, max_depth)
            print(f"{indent}  body:")
            for s in node.get('body', []):
                dump_ast(s, depth + 3, max_depth)
            if node.get('orelse'):
                print(f"{indent}  orelse:")
                for s in node.get('orelse', []):
                    dump_ast(s, depth + 3, max_depth)
        elif t == 'While':
            print(f"{indent}While")
            print(f"{indent}  test:")
            dump_ast(node.get('test'), depth + 3, max_depth)
            print(f"{indent}  body:")
            for s in node.get('body', []):
                dump_ast(s, depth + 3, max_depth)
        elif t == 'Ternary':
            print(f"{indent}Ternary")
            dump_ast(node.get('test'), depth + 2, max_depth)
            dump_ast(node.get('body'), depth + 2, max_depth)
            dump_ast(node.get('orelse'), depth + 2, max_depth)
        else:
            print(f"{indent}{t}: {list(node.keys())}")
    elif isinstance(node, list):
        print(f"{indent}List ({len(node)}):")
        for s in node:
            dump_ast(s, depth + 1, max_depth)
    else:
        print(f"{indent}{node!r}")


def main():
    code_obj = load_code()
    print(f"module code: {code_obj.co_name}")

    cfg = build_cfg(code_obj)
    gen = RegionASTGenerator(cfg, top_level_code=code_obj)
    ast = gen.generate()
    print(f"AST generated: type={type(ast).__name__}")
    if isinstance(ast, dict):
        print(f"  keys: {list(ast.keys())}")
        body = ast.get('body', [])
    else:
        body = ast

    print(f"body has {len(body)} statements")

    # 找到 get_str_data 函数的 AST
    found = False
    for i, node in enumerate(body):
        if isinstance(node, dict) and node.get('type') == 'FunctionDef' and node.get('name') == 'get_str_data':
            found = True
            print(f"=== get_str_data AST (index {i}) ===")
            fbody = node.get('body', [])
            print(f"function body has {len(fbody)} top-level statements")
            for j, s in enumerate(fbody):
                print(f"\n--- stmt {j} ---")
                dump_ast(s, 0, 5)
            break
    if not found:
        print("AST 中未找到 get_str_data FunctionDef")
        for i, node in enumerate(body[:30]):
            print(f"  body[{i}]: {node if not isinstance(node, dict) else node.get('type')}")


if __name__ == '__main__':
    main()
