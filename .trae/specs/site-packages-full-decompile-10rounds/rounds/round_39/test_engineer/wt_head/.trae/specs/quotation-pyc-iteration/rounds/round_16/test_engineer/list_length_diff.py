"""R16: 列出每个失败函数的 length_diff，按 delta 排序。"""
import sys
import types
import marshal
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r15_decompiled.py'

INSTR_DIFF_FUNCS_RAW = [
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
INSTR_DIFF_FUNCS = [f if f == '<module>' else '<module>.' + f for f in INSTR_DIFF_FUNCS_RAW]


def load_pyc_code_objects(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    result = {}
    _collect(code, result, prefix='')
    return result


def _collect(code, result, prefix):
    name = '<module>' if not prefix else prefix + '.' + code.co_name
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


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    rows = []
    for name in INSTR_DIFF_FUNCS:
        if name not in pyc_codes or name not in src_codes:
            continue
        pi = list(dis.get_instructions(pyc_codes[name]))
        si = list(dis.get_instructions(src_codes[name]))
        delta = len(si) - len(pi)
        rows.append((delta, len(pi), len(si), name))

    rows.sort(key=lambda r: r[0])

    print(f"\n=== R16 length_diff 排序（按 delta 升序）===")
    print(f"{'delta':>6} {'pyc':>5} {'src':>5}  name")
    for delta, p, s, name in rows:
        print(f"{delta:>6} {p:>5} {s:>5}  {name}")


if __name__ == '__main__':
    main()
