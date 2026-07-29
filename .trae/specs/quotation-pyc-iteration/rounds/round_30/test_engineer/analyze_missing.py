"""R30 测试工程师：分析失败函数中缺失/多余的指令"""
import sys
import dis
import types
from collections import Counter

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r30_decompiled.py'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    codes = {}
    def collect(co, prefix=''):
        name = prefix + co.co_name
        codes[name] = co
        for c in co.co_consts:
            if isinstance(c, type(co)):
                collect(c, prefix)
    collect(code_obj)
    return codes


def load_src_code_objects(src_path):
    with open(src_path) as f:
        src = f.read()
    codes = {}
    try:
        mod = compile(src, src_path, 'exec')
    except SyntaxError as e:
        print(f"SyntaxError: {e}")
        return None
    def collect(co, prefix=''):
        name = prefix + co.co_name
        codes[name] = co
        for c in co.co_consts:
            if isinstance(c, type(co)):
                collect(c, prefix)
    collect(mod)
    return codes


def get_instr_list(co):
    result = []
    for ins in dis.get_instructions(co):
        result.append((ins.opname, ins.argval))
    return result


def analyze_opname_diff(name, pyc_codes, src_codes):
    """Compare opname frequency between pyc and src to find missing/extra instruction types."""
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = get_instr_list(pc)
    si = get_instr_list(sc)

    pyc_opnames = Counter(op for op, _ in pi)
    src_opnames = Counter(op for op, _ in si)

    all_ops = set(pyc_opnames.keys()) | set(src_opnames.keys())
    print(f"\n=== {name}: pyc={len(pi)} src={len(si)} diff={len(si)-len(pi)} ===")
    print(f"  Opname differences (pyc_count vs src_count, delta):")
    for op in sorted(all_ops):
        pc_count = pyc_opnames[op]
        sc_count = src_opnames[op]
        if pc_count != sc_count:
            delta = sc_count - pc_count
            sign = '+' if delta > 0 else ''
            print(f"    {op:30s} pyc={pc_count:4d} src={sc_count:4d} delta={sign}{delta}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    if src_codes is None:
        return
    targets = sys.argv[1:] if len(sys.argv) > 1 else [
        'load_bars_from_hundsun', 'fill_minute_or_day_blank', '<module>',
        'change_his_to_backward', 'get_str_data', 'get_date_and_count',
        'load_get_price', 'one_prod_to_dataframe',
    ]
    for t in targets:
        if t in pyc_codes and t in src_codes:
            analyze_opname_diff(t, pyc_codes, src_codes)


if __name__ == '__main__':
    main()
