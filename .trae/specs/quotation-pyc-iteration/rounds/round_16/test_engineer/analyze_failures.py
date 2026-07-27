"""R16 测试工程师：分析失败函数的差异模式。

对每个 instr_diff 函数，比较原始 pyc 字节码与反编译源码 recompile 后的字节码，
分类失败模式（如 jump_target_diff, opname_diff, argval_diff, length_diff 等）。
"""
import sys
import types
import marshal
import dis
import os
from collections import defaultdict

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r15_decompiled.py'

# 上一轮 exact_match_stats 输出的 instr_diff 列表（带 <module>. 前缀）
_BASE_FUNCS = [
    '<module>', 'api_get', 'api_get_financial', 'balance_statement',
    'build_future_fill_time', 'change_future_real_date',
    'change_his_to_backward', 'change_his_to_forward', 'check_frequency',
    'check_index_code', 'check_industry_code', 'check_stocks',
    'convert_to_list', 'date_convert', 'fill_minute_or_day_blank',
    'fill_missing_stock_data', 'filter_duplicated_date', 'get_block_stocks',
    'get_cb_calender_info', 'get_cb_info', 'get_cb_time_info',
    'get_date_and_count', 'get_dominant_contract', 'get_fields',
    'get_fundamentals', 'get_fundamentals_daily_info', 'get_fundflow_day',
    'get_holiday_online', 'get_index_stocks', 'get_opt_contracts',
    'get_opt_last_dates', 'get_opt_objects', 'get_option_info', 'get_price',
    'get_quote', 'get_stock_blocks', 'get_stock_exrights', 'get_str_data',
    'get_valuation_info', 'get_valuation_new', 'get_valuation_new_info',
    'isVaildDate', 'load_bars_from_hundsun', 'load_get_exrights',
    'load_get_index_stocks', 'load_get_industry_stocks', 'load_get_price',
    'load_minute_or_day_kline', 'multi_prod_to_dataframe', 'obtain_date',
    'one_prod_to_dataframe', 'share_change', 'valuation', 'valuation_new',
]
INSTR_DIFF_FUNCS = [f if f == '<module>' else '<module>.' + f for f in _BASE_FUNCS]


def load_pyc_code_objects(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    result = {}
    _collect(code, result, prefix='')
    return result


def _collect(code, result, prefix):
    if not prefix:
        name = '<module>'
    else:
        name = prefix + '.' + code.co_name
    result[name] = code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            _collect(c, result, name)


def load_src_code_objects(src_path):
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    try:
        code = compile(src, src_path, 'exec')
    except SyntaxError as e:
        print(f"[load_src] SyntaxError: {e}")
        return None
    result = {}
    _collect(code, result, prefix='')
    return result


def instr_seq(code):
    """返回指令列表 [(opname, argval, offset)]"""
    return [(i.opname, i.argval, i.offset) for i in dis.get_instructions(code)]


def classify_diff(pyc_code, src_code):
    """返回差异分类标签列表"""
    pi = instr_seq(pyc_code)
    si = instr_seq(src_code)
    tags = []

    # 长度差异
    if len(pi) != len(si):
        tags.append(f"length_diff:pyc={len(pi)},src={len(si)},delta={len(si)-len(pi)}")

    # 共同长度内的逐指令差异
    n = min(len(pi), len(si))
    opname_diffs = defaultdict(int)
    argval_diffs = defaultdict(int)
    jump_target_diffs = defaultdict(int)
    for i in range(n):
        pop, parg, poff = pi[i]
        sop, sarg, soff = si[i]
        if pop != sop:
            opname_diffs[f"{pop}_vs_{sop}"] += 1
        elif parg != sarg:
            # 区分跳转目标差异 vs 常量/名称差异
            if pop in ('JUMP_FORWARD', 'JUMP_BACKWARD',
                       'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                       'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
                       'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
                       'FOR_ITER', 'SEND', 'JUMP_IF_TRUE_OR_POP',
                       'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_NOT_EXC_MATCH'):
                # 跳转目标偏移差异
                if isinstance(parg, int) and isinstance(sarg, int):
                    jump_target_diffs[f"delta={sarg-parg}"] += 1
                else:
                    jump_target_diffs[f"p={parg}_s={sarg}"] += 1
            else:
                argval_diffs[f"{pop}"] += 1

    for k, v in sorted(opname_diffs.items(), key=lambda x: -x[1]):
        tags.append(f"opname_diff:{k}(x{v})")
    for k, v in sorted(jump_target_diffs.items(), key=lambda x: -x[1]):
        tags.append(f"jump_target_diff:{k}(x{v})")
    for k, v in sorted(argval_diffs.items(), key=lambda x: -x[1]):
        tags.append(f"argval_diff:{k}(x{v})")

    return tags if tags else ["unknown"]


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    if src_codes is None:
        return

    func_tags = {}
    pattern_count = defaultdict(int)
    pattern_funcs = defaultdict(list)

    for name in INSTR_DIFF_FUNCS:
        if name not in pyc_codes or name not in src_codes:
            continue
        tags = classify_diff(pyc_codes[name], src_codes[name])
        func_tags[name] = tags
        for t in tags:
            # 取主模式（去掉具体数值，保留类别）
            main_pattern = t.split('(')[0]
            pattern_count[main_pattern] += 1
            pattern_funcs[main_pattern].append(name)

    print(f"\n=== R16 失败模式分布 ===")
    print(f"总失败函数数: {len(func_tags)}\n")
    print("--- 模式频率（按出现次数降序）---")
    for pattern, cnt in sorted(pattern_count.items(), key=lambda x: -x[1]):
        print(f"  {cnt:3d}  {pattern}")
    print()
    print("--- 每个模式的函数列表 ---")
    for pattern, funcs in sorted(pattern_funcs.items(), key=lambda x: -len(x[1])):
        print(f"\n  [{pattern}] ({len(funcs)} funcs)")
        for f in funcs[:15]:
            print(f"    - {f}")
        if len(funcs) > 15:
            print(f"    ... and {len(funcs)-15} more")

    print(f"\n--- 每个函数的完整标签 ---")
    for name, tags in func_tags.items():
        print(f"  {name}:")
        for t in tags:
            print(f"    {t}")


if __name__ == '__main__':
    main()
