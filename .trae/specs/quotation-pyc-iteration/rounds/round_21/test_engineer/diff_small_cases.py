"""R21 测试工程师：对比小案例字节码差异，构建最小复现"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r21_decompiled.py'


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


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def show_diff(name, pyc_codes, src_codes, ctx=3):
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = get_instr_list(pc)
    si = get_instr_list(sc)
    print(f"\n=== {name} ===")
    print(f"pyc={len(pi)} src={len(si)}")
    # find first diff
    min_len = min(len(pi), len(si))
    first_diff = None
    for i in range(min_len):
        if pi[i] != si[i]:
            first_diff = i
            break
    if first_diff is None and len(pi) != len(si):
        first_diff = min_len
    if first_diff is None:
        print("  identical")
        return
    start = max(0, first_diff - ctx)
    end_pyc = min(len(pi), first_diff + ctx + 4)
    end_src = min(len(si), first_diff + ctx + 4)
    print(f"  first_diff@{first_diff}")
    print(f"  --- pyc ---")
    for i in range(start, end_pyc):
        marker = '*' if i == first_diff else ' '
        print(f"  {marker} [{i:3d}] {pi[i][0]:4d}  {pi[i][1]:35s} {pi[i][2]!r}")
    print(f"  --- src ---")
    for i in range(start, end_src):
        marker = '*' if i == first_diff else ' '
        print(f"  {marker} [{i:3d}] {si[i][0]:4d}  {si[i][1]:35s} {si[i][2]!r}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    # smallest opname cases
    show_diff('isVaildDate', pyc_codes, src_codes, ctx=5)
    show_diff('load_minute_or_day_kline', pyc_codes, src_codes, ctx=5)
    # smallest jump_target cases
    show_diff('get_quote', pyc_codes, src_codes, ctx=5)
    show_diff('get_index_stocks', pyc_codes, src_codes, ctx=5)
    show_diff('convert_to_list', pyc_codes, src_codes, ctx=5)
    # argval cases
    show_diff('check_index_code', pyc_codes, src_codes, ctx=5)
    show_diff('get_opt_objects', pyc_codes, src_codes, ctx=5)
    show_diff('get_stock_exrights', pyc_codes, src_codes, ctx=5)


if __name__ == '__main__':
    main()
