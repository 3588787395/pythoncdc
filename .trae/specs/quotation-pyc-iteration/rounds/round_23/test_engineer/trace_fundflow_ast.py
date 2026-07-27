"""R23-N4: 跟踪 get_fundflow_day 的反编译过程"""
import sys
import dis
import types
import ast

sys.path.insert(0, '/workspace')

from pycdc import decompile_pyc
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator


PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
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
    co = pyc_codes['get_fundflow_day']

    cfg = build_cfg(co)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    print("=== AST 生成 (Dict) ===")
    gen = RegionASTGenerator(cfg, analyzer)
    result = gen.generate()
    print(f"Result type: {type(result)}")
    if isinstance(result, dict):
        print(f"Keys: {list(result.keys())}")
        # 检查 body
        body = result.get('body', [])
        print(f"Body length: {len(body)}")
        for i, stmt in enumerate(body):
            print(f"  Body[{i}]: {stmt.get('type') if isinstance(stmt, dict) else type(stmt)}")
            if isinstance(stmt, dict):
                # 递归打印
                def dump(node, indent=2):
                    if isinstance(node, dict):
                        t = node.get('type', '?')
                        print(' ' * indent + f"type={t}")
                        for k, v in node.items():
                            if k == 'type':
                                continue
                            if isinstance(v, (dict, list)) and k in ('body', 'orelse', 'test', 'value', 'targets', 'args', 'keywords', 'func', 'iter', 'target', 'items'):
                                print(' ' * indent + f"{k}:")
                                if isinstance(v, list):
                                    for item in v:
                                        dump(item, indent + 2)
                                else:
                                    dump(v, indent + 2)
                    elif isinstance(node, list):
                        for item in node:
                            dump(item, indent)
                    else:
                        print(' ' * indent + f"{node!r}")
                dump(stmt)

    # 单独反编译这个函数
    print("\n=== 单独反编译 get_fundflow_day ===")
    # 创建一个假的模块只包含这个函数
    import inspect
    src = f"""
def get_fundflow_day(prod_code, get_type='range', start_date=None, end_date=None, date=None, search_direction=None, data_count=None, trans_or_order=None):
    pass
"""
    # 直接用 decompile_pyc 反编译整个 pyc
    full_src = decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)
    # 找到 get_fundflow_day 函数
    import re
    match = re.search(r'def get_fundflow_day\(.*?\n(?=\ndef |\Z)', full_src, re.DOTALL)
    if match:
        print(match.group(0))
    else:
        print("未找到 get_fundflow_day 函数")
        # 打印所有 def 行
        for line in full_src.split('\n'):
            if line.startswith('def '):
                print(f"  {line}")


if __name__ == '__main__':
    main()
