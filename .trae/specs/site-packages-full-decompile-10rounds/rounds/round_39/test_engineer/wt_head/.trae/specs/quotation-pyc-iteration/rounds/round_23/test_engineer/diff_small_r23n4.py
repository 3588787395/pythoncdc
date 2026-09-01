"""R23-N4: 分析小函数 length_diff 失败模式"""
import sys
import dis
import types
import ast

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r22_decompiled.py'


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


def load_src_code_objects(src_path):
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    code_obj = compile(src, '<decompiled>', 'exec')
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


def show(name, pyc_codes, src_codes):
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = list(dis.get_instructions(pc))
    si = list(dis.get_instructions(sc))
    pi = [i for i in pi if i.opname not in ('EXTENDED_ARG', 'CACHE')]
    si = [i for i in si if i.opname not in ('EXTENDED_ARG', 'CACHE')]
    print(f"\n{'='*80}")
    print(f"=== {name}: pyc={len(pi)} src={len(si)} ===")
    print(f"{'='*80}")

    print(f"\n--- PYC ---")
    for ins in pi:
        print(f"  {ins.offset:4d}  {ins.opname:35s} {ins.argrepr}")

    print(f"\n--- SRC ---")
    for ins in si:
        print(f"  {ins.offset:4d}  {ins.opname:35s} {ins.argrepr}")

    # 显示反编译源码
    src_text = open(SRC, 'r', encoding='utf-8').read()
    tree = ast.parse(src_text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            print(f"\n--- SRC CODE ---")
            print(ast.unparse(node))
            break


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    # 查看几个小的 length_diff 案例
    for name in ['get_fundflow_day', 'check_index_code', 'check_industry_code']:
        if name in pyc_codes and name in src_codes:
            show(name, pyc_codes, src_codes)


if __name__ == '__main__':
    main()
