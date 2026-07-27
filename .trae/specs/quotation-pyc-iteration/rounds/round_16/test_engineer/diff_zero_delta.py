"""R16: 详细对比 delta=0 失败函数的指令差异。"""
import sys
import types
import marshal
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r15_decompiled.py'

ZERO_DELTA_FUNCS = [
    'check_frequency', 'check_stocks', 'convert_to_list', 'date_convert',
    'fill_missing_stock_data', 'filter_duplicated_date',
    'get_cb_calender_info', 'get_cb_info', 'get_dominant_contract',
    'get_fundamentals', 'get_price', 'get_stock_blocks',
    'load_get_index_stocks', 'load_get_industry_stocks',
    'load_minute_or_day_kline', 'obtain_date',
]


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


def diff_func(pyc_code, src_code):
    pi = list(dis.get_instructions(pyc_code))
    si = list(dis.get_instructions(src_code))
    n = min(len(pi), len(si))
    diffs = []
    for i in range(n):
        p = pi[i]
        s = si[i]
        if p.opname != s.opname or p.argval != s.argval:
            diffs.append((i, p, s))
    return pi, si, diffs


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    for fname in ZERO_DELTA_FUNCS:
        full = '<module>.' + fname
        if full not in pyc_codes or full not in src_codes:
            continue
        pi, si, diffs = diff_func(pyc_codes[full], src_codes[full])
        print(f"\n=== {fname} (pyc={len(pi)}, src={len(si)}, diffs={len(diffs)}) ===")
        for i, p, s in diffs[:10]:
            print(f"  [{i}] pyc:  {p.offset:4d} {p.opname:<30s} {p.argrepr}")
            print(f"        src:  {s.offset:4d} {s.opname:<30s} {s.argrepr}")
        if len(diffs) > 10:
            print(f"  ... {len(diffs)-10} more diffs")


if __name__ == '__main__':
    main()
