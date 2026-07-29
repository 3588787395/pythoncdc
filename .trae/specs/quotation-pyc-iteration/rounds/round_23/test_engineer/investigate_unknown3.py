"""R23-N4: 调查 unknown 失败的嵌套 code object 差异"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r22_decompiled.py'


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
        if ins.opname == 'EXTENDED_ARG':
            continue
        if ins.opname == 'CACHE':
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def find_first_diff(co_a, co_b, path='root'):
    """递归查找首个差异"""
    pi = get_instr_list(co_a)
    si = get_instr_list(co_b)
    if len(pi) != len(si):
        return f"{path}: length_diff pyc={len(pi)} src={len(si)}"
    for i, (a, b) in enumerate(zip(pi, si)):
        if a[1] != b[1]:
            return f"{path}: opname_diff @{a[0]} pyc={a[1]}({a[2]!r}) src={b[1]}({b[2]!r})"
        av_a, av_b = a[2], b[2]
        if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
            sub = find_first_diff(av_a, av_b, f"{path}.{av_a.co_name}")
            if sub:
                return sub
            # 检查 signature
            if av_a.co_name != av_b.co_name:
                return f"{path}: codename_diff pyc={av_a.co_name!r} src={av_b.co_name!r}"
            if av_a.co_varnames != av_b.co_varnames:
                return f"{path}.{av_a.co_name}: varnames pyc={av_a.co_varnames} src={av_b.co_varnames}"
            if av_a.co_argcount != av_b.co_argcount:
                return f"{path}.{av_a.co_name}: argcount pyc={av_a.co_argcount} src={av_b.co_argcount}"
            continue
        if av_a != av_b:
            return f"{path}: argval_diff @{a[0]} op={a[1]} pyc={av_a!r} src={av_b!r}"
    return None


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    UNKNOWN = ['build_current_period_df', 'datetimeindex_astype', 'getLogger',
               'get_date_index', 'get_fundamentals_daily_info', 'get_market_list',
               'get_valuation_info', 'get_valuation_new_info']

    for name in UNKNOWN:
        pc = pyc_codes[name]
        sc = src_codes[name]
        diff = find_first_diff(pc, sc, name)
        print(f"{name}: {diff or 'NO DIFF'}")

        # 也比较 sig
        sig_diffs = []
        if pc.co_argcount != sc.co_argcount: sig_diffs.append(f"argcount {pc.co_argcount} vs {sc.co_argcount}")
        if pc.co_kwonlyargcount != sc.co_kwonlyargcount: sig_diffs.append(f"kwargcount")
        if pc.co_posonlyargcount != sc.co_posonlyargcount: sig_diffs.append(f"posonlyargcount {pc.co_posonlyargcount} vs {sc.co_posonlyargcount}")
        if pc.co_flags != sc.co_flags: sig_diffs.append(f"flags {pc.co_flags} vs {sc.co_flags}")
        if pc.co_varnames != sc.co_varnames: sig_diffs.append(f"varnames {pc.co_varnames} vs {sc.co_varnames}")
        if pc.co_freevars != sc.co_freevars: sig_diffs.append(f"freevars {pc.co_freevars} vs {sc.co_freevars}")
        if pc.co_cellvars != sc.co_cellvars: sig_diffs.append(f"cellvars {pc.co_cellvars} vs {sc.co_cellvars}")
        if pc.co_names != sc.co_names: sig_diffs.append(f"names {pc.co_names} vs {sc.co_names}")
        if sig_diffs:
            print(f"  SIG: {'; '.join(sig_diffs)}")


if __name__ == '__main__':
    main()
