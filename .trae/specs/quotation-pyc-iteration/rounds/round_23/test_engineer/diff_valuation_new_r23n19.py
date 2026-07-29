"""R23-N19: 分析 get_valuation_new 的差异"""
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


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    for name in ['get_valuation_new', 'get_fields', 'get_block_stocks']:
        pa = [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(pyc_codes[name]) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]
        sa = [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(src_codes[name]) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]
        print(f"\n=== {name} PYC vs SRC (p={len(pa)}, s={len(sa)}) ===")
        max_len = max(len(pa), len(sa))
        first_diff = None
        for i in range(max_len):
            a = pa[i] if i < len(pa) else None
            b = sa[i] if i < len(sa) else None
            if a is None or b is None or a[1] != b[1] or a[2] != b[2]:
                first_diff = i
                break
        if first_diff is None:
            print("  完全一致")
            continue
        start = max(0, first_diff - 5)
        end = min(max_len, first_diff + 25)
        for i in range(start, end):
            a = pa[i] if i < len(pa) else None
            b = sa[i] if i < len(sa) else None
            a_str = f"{a[0]:4d} {a[1]:30s} {a[3]}" if a else "(none)"
            b_str = f"{b[0]:4d} {b[1]:30s} {b[3]}" if b else "(none)"
            match = "OK" if a and b and a[1] == b[1] and a[2] == b[2] else "!!"
            print(f"  {match} a: {a_str}")
            print(f"  {match} b: {b_str}")

        import re
        with open(SRC, 'r') as f:
            src = f.read()
        match = re.search(rf'def {name}\(.*?\n(?=\ndef |\Z|@)', src, re.DOTALL)
        if match:
            print(f"\n--- 反编译源码 ---")
            print(match.group(0)[:2000])


if __name__ == '__main__':
    main()
