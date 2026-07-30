"""R24 测试工程师：dump 两个残留函数的 orig vs new 字节码。"""
import sys, types, dis, os, json
sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r24_decompiled.py'

from core.pyc_loader_v2 import load_pyc_file_v2


def load_orig():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    return code_obj


def walk_code(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    name = '<module>' if (co.co_name == '<module>' and not prefix) else prefix + co.co_name
    sink[name] = co
    sub_prefix = '' if name == '<module>' else name + '.'
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            walk_code(const, sub_prefix, sink)
    return sink


def main():
    orig_top = load_orig()
    orig_cos = walk_code(orig_top)
    with open(DECOMPILED, 'r', encoding='utf-8') as f:
        src = f.read()
    new_code = compile(src, '<decompiled>', 'exec')
    new_cos = walk_code(new_code)

    targets = ['change_his_to_backward', 'get_date_and_count']
    for name in targets:
        print(f"\n{'='*100}")
        print(f"FUNCTION: {name}")
        print(f"{'='*100}")
        if name in orig_cos:
            print(f"\n--- ORIG bytecode (offsets) for {name} ---")
            dis.dis(orig_cos[name], show_caches=False)
        if name in new_cos:
            print(f"\n--- NEW bytecode (offsets) for {name} ---")
            dis.dis(new_cos[name], show_caches=False)


if __name__ == '__main__':
    main()
