"""R24-N1 调试：change_his_to_forward 跳转目标差异 -2"""
import sys
import importlib.util
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


pyc_codes = load_pyc_code_objects(PYC)
src_codes = load_src_code_objects(SRC)

for name in ['change_his_to_forward', 'get_option_info', 'get_cb_time_info', 'share_change', 'get_fields', 'get_valuation_new', 'build_future_fill_time']:
    print(f"\n=== {name} ===")
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(pc) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]
    si = [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(sc) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]

    first_diff = None
    for i in range(max(len(pi), len(si))):
        a = pi[i] if i < len(pi) else None
        b = si[i] if i < len(si) else None
        if not (a and b and a[1] == b[1] and a[2] == b[2]):
            first_diff = i
            break

    if first_diff is None:
        print("IDENTICAL")
        continue

    print(f"First diff at index {first_diff}:")
    start = max(0, first_diff - 5)
    end = min(max(len(pi), len(si)), first_diff + 30)
    for i in range(start, end):
        a = pi[i] if i < len(pi) else None
        b = si[i] if i < len(si) else None
        a_str = f"p: {a[0]:4d} {a[1]:30s} {a[3]}" if a else "p: (none)"
        b_str = f"s: {b[0]:4d} {b[1]:30s} {b[3]}" if b else "s: (none)"
        match = "OK" if a and b and a[1] == b[1] and a[2] == b[2] else "!!"
        print(f"  [{i:3d}] {match} {a_str}")
        print(f"         {match} {b_str}")
