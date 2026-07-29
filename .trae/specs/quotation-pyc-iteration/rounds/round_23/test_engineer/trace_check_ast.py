"""R23-N4: 查看检查 check_index_code 的 AST 结构"""
import sys
import types

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

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


def print_if(if_node, indent=0):
    prefix = ' ' * indent
    test = if_node.get('test', {})
    print(f"{prefix}If (is_elif={if_node.get('_is_elif')})")
    print(f"{prefix}  test: {test.get('type') if isinstance(test, dict) else type(test).__name__}")
    body = if_node.get('body', [])
    print(f"{prefix}  body: {[b.get('type') if isinstance(b, dict) else type(b).__name__ for b in body]}")
    orelse = if_node.get('orelse', [])
    print(f"{prefix}  orelse: {len(orelse)} items")
    for k, oe in enumerate(orelse):
        if isinstance(oe, dict) and oe.get('type') == 'If':
            print(f"{prefix}  orelse[{k}]:")
            print_if(oe, indent + 4)
        else:
            print(f"{prefix}  orelse[{k}]: {oe.get('type') if isinstance(oe, dict) else type(oe).__name__}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    co = pyc_codes['check_index_code']

    cfg = build_cfg(co)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    ast_dict = gen.generate()

    print(f"=== generate() 返回 ===")
    print(f"  type: {ast_dict.get('type') if isinstance(ast_dict, dict) else type(ast_dict).__name__}")
    if isinstance(ast_dict, dict):
        if ast_dict.get('type') == 'FunctionDef':
            body = ast_dict.get('body', [])
            print(f"  FunctionDef: {ast_dict.get('name')}")
            print(f"  body has {len(body)} nodes")
            for i, node in enumerate(body):
                print(f"\n  body[{i}]:")
                if isinstance(node, dict) and node.get('type') == 'If':
                    print_if(node, indent=4)
                else:
                    print(f"    {node.get('type') if isinstance(node, dict) else type(node).__name__}")
        else:
            body = ast_dict.get('body', [])
            print(f"  body has {len(body)} nodes")
            for i, node in enumerate(body):
                print(f"  body[{i}]: {node.get('type') if isinstance(node, dict) else type(node).__name__}")


if __name__ == '__main__':
    main()
