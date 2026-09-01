"""R30 测试工程师：详细分析小差异函数"""
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
        return ('<code>', argval.co_name, argval.co_code)
    return argval


def get_instr_list_normalized(co):
    result = []
    for ins in dis.get_instructions(co):
        argval = normalize_argval(ins.argval)
        result.append((ins.opname, argval))
    return result


def show_diff(name, pyc_codes, src_codes):
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
            print(f"  pyc tail: {pi[min_len:]}")
        if len(si) > min_len:
            print(f"  src tail: {si[min_len:]}")
        return
    print(f"  diff count: {len(diffs)}, range: {diffs[0]}..{diffs[-1]}")
    for i in diffs:
        p = pi[i]
        s = si[i]
        p_show = repr(p[1])[:60]
        s_show = repr(s[1])[:60]
        print(f"  >> idx={i}: pyc={p[0]} {p_show} | src={s[0]} {s_show}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    for name in ['get_option_info', 'change_his_to_forward', 'get_cb_time_info', 'get_block_stocks']:
        show_diff(name, pyc_codes, src_codes)


if __name__ == '__main__':
    main()
