"""R23-N4: 查看 check_index_code 第三个 elif 的完整 AST dict"""
import sys
import types
import json

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


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    co = pyc_codes['check_index_code']

    cfg = build_cfg(co)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    ast_dict = gen.generate()

    # 找到最深的 elif
    body = ast_dict.get('body', [])
    cur = body[0]  # outer If
    depth = 0
    while cur:
        print(f"\n=== depth {depth} If ===")
        print(f"  keys: {list(cur.keys())}")
        print(f"  _is_elif: {cur.get('_is_elif')}")
        print(f"  has elif_test: {'elif_test' in cur}")
        print(f"  has elif_body: {'elif_body' in cur}")
        print(f"  has final_else: {'final_else' in cur}")
        if 'final_else' in cur:
            print(f"  final_else: {cur['final_else']}")
        orelse = cur.get('orelse', [])
        print(f"  orelse: {len(orelse)} items, types: {[o.get('type') if isinstance(o, dict) else type(o).__name__ for o in orelse]}")
        if orelse and isinstance(orelse[0], dict) and orelse[0].get('type') == 'If':
            cur = orelse[0]
            depth += 1
        else:
            # 最深 elif
            print(f"\n=== 最深 elif (depth {depth}) 的完整 orelse ===")
            for j, oe in enumerate(orelse):
                print(f"\norelse[{j}]:")
                if isinstance(oe, dict):
                    # 打印所有字段
                    for k, v in oe.items():
                        if isinstance(v, dict):
                            print(f"  {k}: dict type={v.get('type')}")
                        elif isinstance(v, list):
                            print(f"  {k}: list of {len(v)} items")
                        else:
                            print(f"  {k}: {v!r}")
                else:
                    print(f"  {type(oe).__name__}")
            break


if __name__ == '__main__':
    main()
