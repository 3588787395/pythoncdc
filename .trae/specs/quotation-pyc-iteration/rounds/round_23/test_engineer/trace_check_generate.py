"""R23-N4: 跟踪 generate() 对 check_index_code 的处理"""
import sys
import types
import json

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole, RegionType, IfRegion, BoolOpRegion, TernaryRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion, Region
from core.cfg.region_ast_generator import RegionASTGenerator
from pycdc import decompile_pyc

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

    # Monkey-patch _generate_region
    original_gen_region = gen._generate_region
    def traced_gen_region(region, skip_store_targets=None):
        print(f"\n[_generate_region] region={type(region).__name__}@{region.entry.start_offset if region.entry else None} (type={region.region_type.name})")
        result = original_gen_region(region, skip_store_targets)
        if isinstance(result, list):
            print(f"  RESULT: list of {len(result)} items: {[s.get('type') if isinstance(s, dict) else type(s).__name__ for s in result]}")
        elif isinstance(result, dict):
            print(f"  RESULT: {result.get('type')}")
        else:
            print(f"  RESULT: {type(result).__name__}")
        return result
    gen._generate_region = traced_gen_region

    # 调用 generate()
    print("=== 调用 generate() ===")
    ast_dict = gen.generate()
    print(f"\n=== generate() 返回 ===")
    print(f"  type: {ast_dict.get('type') if isinstance(ast_dict, dict) else type(ast_dict).__name__}")
    if isinstance(ast_dict, dict):
        body = ast_dict.get('body', [])
        print(f"  body has {len(body)} nodes")
        for i, node in enumerate(body):
            if isinstance(node, dict):
                print(f"  body[{i}]: type={node.get('type')}")

    # 深入查看 body
    if isinstance(ast_dict, dict):
        body = ast_dict.get('body', [])
        for i, node in enumerate(body):
            if isinstance(node, dict) and node.get('type') == 'FunctionDef' and node.get('name') == 'check_index_code':
                # 找到 check_index_code
                fbody = node.get('body', [])
                print(f"\n=== check_index_code body ({len(fbody)} nodes) ===")
                for j, n in enumerate(fbody):
                    print(f"  body[{j}]: {n.get('type') if isinstance(n, dict) else type(n).__name__}")
                    if isinstance(n, dict) and n.get('type') == 'If':
                        # 递归打印 If 结构
                        def print_if(if_node, indent=2):
                            prefix = ' ' * indent
                            test = if_node.get('test', {})
                            print(f"{prefix}test: {test.get('type') if isinstance(test, dict) else type(test).__name__}")
                            body = if_node.get('body', [])
                            print(f"{prefix}body: {[b.get('type') if isinstance(b, dict) else type(b).__name__ for b in body]}")
                            orelse = if_node.get('orelse', [])
                            print(f"{prefix}orelse: {len(orelse)} items")
                            for k, oe in enumerate(orelse):
                                if isinstance(oe, dict) and oe.get('type') == 'If':
                                    print(f"{prefix}  orelse[{k}]: If (_is_elif={oe.get('_is_elif')})")
                                    print_if(oe, indent + 4)
                                else:
                                    print(f"{prefix}  orelse[{k}]: {oe.get('type') if isinstance(oe, dict) else type(oe).__name__}")
                        print_if(n)


if __name__ == '__main__':
    main()
