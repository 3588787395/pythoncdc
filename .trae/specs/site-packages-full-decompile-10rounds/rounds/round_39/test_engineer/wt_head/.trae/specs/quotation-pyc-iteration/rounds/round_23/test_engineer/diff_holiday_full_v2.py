"""R23-N20: 详细分析get_holiday_online函数的完整指令差异"""
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


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname == 'EXTENDED_ARG':
            continue
        if ins.opname == 'CACHE':
            continue
        instrs.append((ins.offset, ins.opname, ins.argval, ins.argrepr))
    return instrs


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    name = 'get_holiday_online'
    pa = get_instr_list(pyc_codes[name])
    sa = get_instr_list(src_codes[name])
    print(f"=== {name} PYC vs SRC (p={len(pa)}, s={len(sa)}) ===\n")

    # 全量打印
    max_len = max(len(pa), len(sa))
    print(f"{'idx':>4} | {'p_off':>5} {'p_op':30s} {'p_arg':>20} | {'s_off':>5} {'s_op':30s} {'s_arg':>20} | {'match':4}")
    print('-' * 130)
    for i in range(max_len):
        a = pa[i] if i < len(pa) else None
        b = sa[i] if i < len(sa) else None
        a_str = f"{a[0]:5d} {a[1]:30s} {a[3]:>20}" if a else f"{'':>5} {'':30s} {'':>20}"
        b_str = f"{b[0]:5d} {b[1]:30s} {b[3]:>20}" if b else f"{'':>5} {'':30s} {'':>20}"
        if a is None or b is None:
            match = "MISS"
        elif a[1] == b[1] and a[2] == b[2]:
            match = "OK"
        else:
            match = "DIFF"
        marker = "  " if match == "OK" else ">>"
        print(f"{marker}{i:4d} | {a_str} | {b_str} | {match}")

    # 反编译源码
    import re
    with open(SRC, 'r') as f:
        src = f.read()
    match = re.search(rf'def {name}\(.*?\n(?=\ndef |\Z|@)', src, re.DOTALL)
    if match:
        print(f"\n--- 反编译源码 ---")
        print(match.group(0))


if __name__ == '__main__':
    main()
