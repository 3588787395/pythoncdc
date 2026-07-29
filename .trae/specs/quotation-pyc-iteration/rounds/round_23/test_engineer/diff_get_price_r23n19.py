"""R23-N19: 分析 get_price 的字节码差异"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'


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


def show_diff(co_a, co_b, label_a, label_b):
    ia = [(ins.offset, ins.opname, ins.argval) for ins in dis.get_instructions(co_a) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]
    ib = [(ins.offset, ins.opname, ins.argval) for ins in dis.get_instructions(co_b) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]
    print(f"\n=== {label_a} vs {label_b} (a={len(ia)}, b={len(ib)}) ===")
    # 找到第一个差异
    max_len = max(len(ia), len(ib))
    first_diff = None
    for i in range(max_len):
        a = ia[i] if i < len(ia) else None
        b = ib[i] if i < len(ib) else None
        if a is None or b is None or a[1] != b[1] or a[2] != b[2]:
            first_diff = i
            break
    if first_diff is None:
        print("  完全一致")
        return
    start = max(0, first_diff - 5)
    end = min(max_len, first_diff + 20)
    for i in range(start, end):
        a = ia[i] if i < len(ia) else None
        b = ib[i] if i < len(ib) else None
        a_str = f"{a[0]:4d} {a[1]:25s} {a[2]}" if a else "(none)"
        b_str = f"{b[0]:4d} {b[1]:25s} {b[2]}" if b else "(none)"
        match = "  " if a and b and a[1] == b[1] and a[2] == b[2] else "!!"
        print(f"  {match} a: {a_str}")
        print(f"  {match} b: {b_str}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    for name in ['get_price']:
        show_diff(pyc_codes[name], src_codes[name], f"{name} PYC", f"{name} SRC")
        print(f"\n--- 反编译源码 ---")
        import re
        with open(SRC, 'r') as f:
            src = f.read()
        match = re.search(rf'def {name}\(.*?\n(?=\ndef |\Z|@)', src, re.DOTALL)
        if match:
            print(match.group(0))
        else:
            print(f"未找到 {name}")


if __name__ == '__main__':
    main()
