"""R23 测试工程师：分析多个失败函数的指令差异"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r22_decompiled.py'


def load_pyc_code_objects(pyc_path):
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


def show_diff(name, pyc_codes, src_codes, max_lines=80):
    if name not in pyc_codes or name not in src_codes:
        print(f"[SKIP] {name} not found")
        return
    pc = pyc_codes[name]
    sc = src_codes[name]
    print(f"\n{'='*70}")
    print(f"=== {name} ===")

    pi = list(dis.get_instructions(pc))
    si = list(dis.get_instructions(sc))

    pi2 = [i for i in pi if i.opname not in ('EXTENDED_ARG', 'CACHE')]
    si2 = [i for i in si if i.opname not in ('EXTENDED_ARG', 'CACHE')]

    # find first diff
    first_diff = None
    for i in range(min(len(pi2), len(si2))):
        a, b = pi2[i], si2[i]
        if a.opname != b.opname or a.argval != b.argval:
            first_diff = i
            break

    start = max(0, first_diff - 5 if first_diff else 0)
    end = min(max(len(pi2), len(si2)), (first_diff + 30 if first_diff else 30))
    print(f"  pyc={len(pi2)} src={len(si2)} first_diff@{first_diff}")
    print(f"  --- showing [{start}, {end}) ---")
    for i in range(start, end):
        a = pi2[i] if i < len(pi2) else None
        b = si2[i] if i < len(si2) else None
        mark = ''
        if a and b:
            if a.opname != b.opname or a.argval != b.argval:
                mark = '  <<< DIFF'
        elif a or b:
            mark = '  <<< LEN_DIFF'
        a_str = f"{a.offset:4d} {a.opname:35s} {a.argval!r}" if a else f"{'':4s} {'(none)':35s}"
        b_str = f"{b.offset:4d} {b.opname:35s} {b.argval!r}" if b else f"{'':4s} {'(none)':35s}"
        print(f"  [{i:3d}] PYC: {a_str}")
        print(f"        SRC: {b_str}{mark}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    # Simple cases first
    targets = [
        'convert_to_list',        # 66 vs 66, jump_target
        'get_trading_day_by_date', # 44 vs 46, jump_target
        'get_fundflow_day',        # 67 vs 43, big diff
        'get_holiday_online',      # 113 vs 112, small diff
        'get_block_stocks',        # 106 vs 96
        'get_index_stocks',        # 73 vs 75
        'multi_prod_to_dataframe', # 74 vs 76
    ]
    for n in targets:
        show_diff(n, pyc_codes, src_codes)


if __name__ == '__main__':
    main()
