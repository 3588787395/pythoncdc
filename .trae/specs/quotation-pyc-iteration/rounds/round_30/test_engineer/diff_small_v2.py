"""R30 测试工程师：分析最小差异失败函数"""
import sys
import dis
import types

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


def normalize_argval(argval):
    if isinstance(argval, types.CodeType):
        return (argval.co_name, argval.co_code)
    return argval


def get_instr_list_normalized(co):
    result = []
    for ins in dis.get_instructions(co):
        argval = normalize_argval(ins.argval)
        result.append((ins.opname, argval))
    return result


def show_diff(name, pyc_codes, src_codes, max_show=100):
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = get_instr_list_normalized(pc)
    si = get_instr_list_normalized(sc)
    print(f"\n=== {name}: pyc={len(pi)} src={len(si)} diff={len(si)-len(pi)} ===")
    min_len = min(len(pi), len(si))
    diffs = []
    for i in range(min_len):
        if pi[i] != si[i]:
            diffs.append(i)
    if not diffs:
        if len(pi) > min_len:
            print(f"  pyc tail ({len(pi)-min_len}):")
            for i in range(min_len, min(min_len+max_show, len(pi))):
                print(f"    pyc[{i}]: {pi[i][0]} {repr(pi[i][1])[:80]}")
        if len(si) > min_len:
            print(f"  src tail ({len(si)-min_len}):")
            for i in range(min_len, min(min_len+max_show, len(si))):
                print(f"    src[{i}]: {si[i][0]} {repr(si[i][1])[:80]}")
        return
    print(f"  diff count: {len(diffs)}, range: {diffs[0]}..{diffs[-1]}")
    ctx = 5
    shown_ranges = set()
    for i in diffs[:60]:
        lo = max(0, i - ctx)
        hi = min(min_len, i + ctx + 1)
        if (lo, hi) in shown_ranges:
            continue
        shown_ranges.add((lo, hi))
        print(f"  -- around idx {i} --")
        for j in range(lo, hi):
            p_show = repr(pi[j][1])[:60]
            s_show = repr(si[j][1])[:60]
            mark = '>>' if pi[j] != si[j] else '  '
            print(f"  {mark} [{j}] pyc: {pi[j][0]:18s} {p_show}")
            print(f"  {mark}     src: {si[j][0]:18s} {s_show}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    if src_codes is None:
        return
    # Smallest diffs first
    targets = ['get_option_info', 'change_his_to_forward', 'get_cb_time_info',
               'build_future_fill_time', 'share_change', 'load_get_price']
    for t in targets:
        if t in pyc_codes and t in src_codes:
            show_diff(t, pyc_codes, src_codes)


if __name__ == '__main__':
    main()
