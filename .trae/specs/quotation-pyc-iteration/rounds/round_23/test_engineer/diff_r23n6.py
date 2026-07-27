"""R23-N6: 详细对比失败函数的指令序列，找出关键差异模式"""
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
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def diff_function(name, pyc_codes, src_codes, n_context=8, max_diffs=8):
    """详细对比函数字节码，显示前n个差异及上下文"""
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = get_instr_list(pc)
    si = get_instr_list(sc)
    print(f"\n{'='*80}\n{name}: pyc={len(pi)} instrs, src={len(si)} instrs\n{'='*80}")
    # 找差异
    diff_indices = []
    n = min(len(pi), len(si))
    for i in range(n):
        if pi[i][1] != si[i][1] or pi[i][2] != si[i][2]:
            diff_indices.append(i)
            if len(diff_indices) >= max_diffs:
                break
    if not diff_indices and len(pi) != len(si):
        diff_indices.append(n)
    if not diff_indices:
        print("  (无差异)")
        return
    # 显示每个差异点上下文
    for di in diff_indices:
        start = max(0, di - n_context)
        end_p = min(len(pi), di + n_context + 1)
        end_s = min(len(si), di + n_context + 1)
        print(f"\n  -- 差异点 idx={di} --")
        print(f"  [PYC]")
        for j in range(start, end_p):
            mark = ">>" if j == di else "  "
            print(f"  {mark} {pi[j][0]:>5} {pi[j][1]:<30} {pi[j][2]!r}")
        print(f"  [SRC]")
        for j in range(start, end_s):
            mark = ">>" if j == di else "  "
            print(f"  {mark} {si[j][0]:>5} {si[j][1]:<30} {si[j][2]!r}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    # 选择有代表性的失败函数
    targets = [
        'api_get',                       # src=JUMP_FORWARD 多余
        'get_fields',                    # src=JUMP_FORWARD 多余
        'get_holiday_online',            # src=JUMP_FORWARD 多余
        'date_convert',                  # argval_diff
        'get_option_info',               # JUMP_BACKWARD 差异
        'valuation_new',                 # JUMP_BACKWARD -> NOP
        'one_prod_to_dataframe',         # GET_ITER -> POP_TOP
        'multi_prod_to_dataframe',       # src=NOP
        'get_str_data',                  # STORE_FAST -> LOAD_CONST
        'api_get_financial',             # SWAP -> POP_TOP
    ]
    for t in targets:
        if t in pyc_codes and t in src_codes:
            diff_function(t, pyc_codes, src_codes)


if __name__ == '__main__':
    main()
