"""R30 测试工程师：分析多个失败函数的指令差异"""
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
    mod = compile(src, src_path, 'exec')
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


def show_diff(name, pyc_codes, src_codes, max_show=80):
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
    # Find longest common prefix and suffix
    prefix = 0
    while prefix < min_len and pi[prefix] == si[prefix]:
        prefix += 1
    suffix = 0
    while suffix < min_len - prefix and pi[min_len-1-suffix] == si[min_len-1-suffix]:
        suffix += 1
    print(f"  common prefix: {prefix}, common suffix: {suffix}")
    print(f"  pyc[{prefix}:{min_len-suffix}]: {min_len-suffix-prefix} instrs")
    for i in range(prefix, min(min_len-suffix, prefix+max_show)):
        print(f"    pyc[{i}]: {pi[i][0]:18s} {repr(pi[i][1])[:70]}")
    print(f"  src[{prefix}:{min_len-suffix}]: {min_len-suffix-prefix} instrs")
    for i in range(prefix, min(min_len-suffix, prefix+max_show)):
        print(f"    src[{i}]: {si[i][0]:18s} {repr(si[i][1])[:70]}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    targets = sys.argv[1:] if len(sys.argv) > 1 else ['build_future_fill_time', 'share_change']
    for t in targets:
        if t in pyc_codes and t in src_codes:
            show_diff(t, pyc_codes, src_codes)


if __name__ == '__main__':
    main()
