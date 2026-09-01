"""R29 测试工程师：分类19个失败函数的字节码差异类型"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r27_decompiled.py'

FAILURES = [
    '<module>',
    'build_future_fill_time',
    'change_his_to_backward',
    'change_his_to_forward',
    'fill_minute_or_day_blank',
    'get_block_stocks',
    'get_cb_calender_info',
    'get_cb_time_info',
    'get_date_and_count',
    'get_fields',
    'get_option_info',
    'get_stock_exrights',
    'get_str_data',
    'get_valuation_new',
    'load_bars_from_hundsun',
    'load_get_price',
    'one_prod_to_dataframe',
    'share_change',
    'valuation_new',
]


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


def categorize_diff(name, pi, si):
    """分类差异类型"""
    if len(pi) == 0 or len(si) == 0:
        return 'empty'
    min_len = min(len(pi), len(si))
    first_diff = min_len
    for i in range(min_len):
        if pi[i][1] != si[i][1] or pi[i][2] != si[i][2]:
            first_diff = i
            break

    if first_diff == min_len:
        if len(pi) == len(si):
            return 'identical'
        return f'length_diff(pyc={len(pi)},src={len(si)})'

    p_op = pi[first_diff][1]
    s_op = si[first_diff][1]
    p_arg = pi[first_diff][2]
    s_arg = si[first_diff][2]

    # 跳转目标差异
    if 'JUMP' in p_op or 'POP_JUMP' in p_op:
        if p_op == s_op:
            return f'jump_target_diff({p_op}: pyc={p_arg} src={s_arg})'
        return f'jump_op_diff(pyc={p_op} src={s_op})'

    # 操作符差异
    if p_op != s_op:
        return f'op_diff(pyc={p_op} src={s_op})'

    # 参数差异
    return f'arg_diff({p_op}: pyc={p_arg} src={s_arg})'


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    categories = {}
    details = []
    for name in FAILURES:
        if name not in pyc_codes or name not in src_codes:
            print(f"  {name}: SKIPPED (not found)")
            continue
        pi = get_instr_list(pyc_codes[name])
        si = get_instr_list(src_codes[name])
        cat = categorize_diff(name, pi, si)
        categories.setdefault(cat, []).append(name)
        details.append((name, cat, len(pi), len(si), pi, si))

    print(f"\n=== 差异分类统计 ===")
    for cat, names in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"\n[{cat}] ({len(names)}个):")
        for n in names:
            print(f"  - {n}")

    # 详细展示每种分类的第一个例子
    print(f"\n\n=== 每类首例详细差异 ===")
    for cat, names in sorted(categories.items(), key=lambda x: -len(x[1])):
        name = names[0]
        for d in details:
            if d[0] == name:
                _, _, lp, ls, pi, si = d
                min_len = min(len(pi), len(si))
                first_diff = min_len
                for i in range(min_len):
                    if pi[i][1] != si[i][1] or pi[i][2] != si[i][2]:
                        first_diff = i
                        break
                print(f"\n--- {name} (cat={cat}, pyc={lp}, src={ls}, first_diff={first_diff}) ---")
                start = max(0, first_diff - 3)
                end = min(min_len, first_diff + 8)
                for i in range(start, end):
                    m = '  ' if (pi[i][1] == si[i][1] and pi[i][2] == si[i][2]) else '>>'
                    print(f"{m} {i:<4} pyc={pi[i][0]:>4} {pi[i][1]:<28} {str(pi[i][2])[:25]:<25} | src={si[i][0]:>4} {si[i][1]:<28} {str(si[i][2])[:25]}")
                break


if __name__ == '__main__':
    main()
