"""R23-N8 测试工程师：详细分析小差异失败函数的字节码差异"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'


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


def diff_function(name, pyc_codes, src_codes, max_diffs=20):
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = get_instr_list(pc)
    si = get_instr_list(sc)
    print(f"\n=== {name} (pyc={len(pi)}, src={len(si)}) ===")
    # Use difflib for sequence alignment
    import difflib
    sm = difflib.SequenceMatcher(None, [x[1] for x in pi], [x[1] for x in si])
    diffs_shown = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        print(f"  [{tag}] pyc[{i1}:{i2}] src[{j1}:{j2}]")
        for k in range(i1, i2):
            if k < len(pi):
                off, op, av = pi[k]
                av_s = repr(av)[:60]
                print(f"    P: {off:>6} {op:<25} {av_s}")
        for k in range(j1, j2):
            if k < len(si):
                off, op, av = si[k]
                av_s = repr(av)[:60]
                print(f"    S: {off:>6} {op:<25} {av_s}")
        diffs_shown += 1
        if diffs_shown >= max_diffs:
            print("  ... (truncated)")
            break


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    # Start with the smallest diffs
    targets = [
        'date_convert',
        'get_holiday_online',
        'get_price',
        'get_cb_calender_info',
        'get_index_stocks',
        'multi_prod_to_dataframe',
        'load_get_exrights',
        'get_fields',
        'get_cb_time_info',
    ]
    for name in targets:
        if name in pyc_codes and name in src_codes:
            diff_function(name, pyc_codes, src_codes)


if __name__ == '__main__':
    main()
