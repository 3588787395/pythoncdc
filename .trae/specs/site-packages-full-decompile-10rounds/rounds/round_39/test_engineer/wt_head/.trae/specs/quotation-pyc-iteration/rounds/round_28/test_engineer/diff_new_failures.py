"""R28 测试工程师：检查新增失败函数的差异"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r27_decompiled.py'


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
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def show_full_diff(name, pyc_codes, src_codes):
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = get_instr_list(pc)
    si = get_instr_list(sc)
    print(f"\n{'='*100}")
    print(f"=== {name} (pyc={len(pi)}, src={len(si)}) ===")
    print(f"{'='*100}")
    min_len = min(len(pi), len(si))
    first_diff = min_len
    for i in range(min_len):
        if pi[i][1] != si[i][1] or pi[i][2] != si[i][2]:
            first_diff = i
            break
    print(f"第一个差异在 idx={first_diff}")
    start = max(0, first_diff - 5)
    end = min(min_len, first_diff + 20)
    print(f"  {'idx':<5} {'PYC':<60} {'SRC':<60}")
    for i in range(start, end):
        p = pi[i]
        s = si[i]
        marker = '  ' if (p[1] == s[1] and p[2] == s[2]) else '>>'
        p_str = f"{p[0]:>4} {p[1]:<28} {str(p[2])[:28]}"
        s_str = f"{s[0]:>4} {s[1]:<28} {str(s[2])[:28]}"
        print(f"{marker} {i:<5} {p_str:<60} {s_str:<60}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    # 新增失败函数
    NEW_FAILURES = [
        'cash_collection_ability',
        'cashflow_statement',
        'debt_paying_ability',
        'eps',
        'growth_ability',
        'income_statement',
        'operating_ability',
        'profit_ability',
    ]

    for name in NEW_FAILURES:
        if name in pyc_codes and name in src_codes:
            show_full_diff(name, pyc_codes, src_codes)
        else:
            print(f"\n=== {name}: SKIPPED (not found) ===")


if __name__ == '__main__':
    main()
