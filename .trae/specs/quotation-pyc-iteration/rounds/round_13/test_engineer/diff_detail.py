"""R13 测试工程师：详细分析失败函数的首个指令差异点。

对每个 instr_diff 函数，找到首个不同的指令及其上下文，并按差异模式分类。
"""
import sys
import types
import marshal
import dis
from collections import Counter

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r13_decompiled.py'


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


def code_normalize(code):
    norm_consts = []
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            norm_consts.append(code_normalize(c))
        else:
            norm_consts.append(c)
    return (
        code.co_code,
        tuple(norm_consts),
        code.co_argcount,
        code.co_posonlyargcount,
        code.co_kwonlyargcount,
        code.co_nlocals,
        tuple(code.co_cellvars),
        tuple(code.co_freevars),
        tuple(code.co_varnames),
        tuple(code.co_names),
        code.co_stacksize,
        code.co_flags,
    )


def code_normalize_instr_only(code):
    norm_consts = []
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            norm_consts.append(code_normalize_instr_only(c))
        else:
            norm_consts.append(c)
    return (code.co_code, tuple(norm_consts))


def get_instr_list(code):
    """返回 (offset, opname, argval) 列表（递归到子 code object 时只列顶层）。"""
    instrs = []
    for ins in dis.get_instructions(code):
        instrs.append((ins.offset, ins.opname, repr(ins.argval)[:60]))
    return instrs


def find_first_diff(pc, sc):
    """找两个 code object 的首个指令差异，返回 (idx, pyc_instr, src_instr, pyc_context, src_context)。"""
    pi = get_instr_list(pc)
    si = get_instr_list(sc)
    n = min(len(pi), len(si))
    for i in range(n):
        if pi[i] != si[i]:
            pctx = pi[max(0, i-3):i+4]
            sctx = si[max(0, i-3):i+4]
            return (i, pi[i], si[i], pctx, sctx)
    if len(pi) != len(si):
        if len(pi) > len(si):
            return (n, pi[n], None, pi[max(0, n-3):n+4], si[max(0, n-3):n+4])
        else:
            return (n, None, si[n], pi[max(0, n-3):n+4], si[max(0, n-3):n+4])
    return None


def classify_diff(pyc_instr, src_instr, pyc_ctx, src_ctx):
    """根据首个差异指令对分类失败模式。"""
    if pyc_instr is None:
        return 'src_extra_instr'
    if src_instr is None:
        return 'pyc_extra_instr'
    p_op = pyc_instr[1]
    s_op = src_instr[1]
    if p_op != s_op:
        # 检查是否是 RETURN_VALUE vs POP_TOP（return 丢失）
        if p_op == 'RETURN_VALUE' and s_op == 'POP_TOP':
            return 'return_lost_to_pop_top'
        if p_op == 'RETURN_CONST' and s_op == 'POP_TOP':
            return 'return_const_lost_to_pop_top'
        if p_op == 'POP_TOP' and s_op in ('RETURN_VALUE', 'RETURN_CONST'):
            return 'spurious_return'
        # JUMP 方向差异
        if 'JUMP' in p_op and 'JUMP' in s_op:
            return f'jump_diff:{p_op}->{s_op}'
        # STORE vs LOAD 顺序
        if p_op.startswith('STORE') and s_op.startswith('STORE'):
            return 'store_order_diff'
        if p_op.startswith('LOAD') and s_op.startswith('LOAD'):
            return 'load_order_diff'
        return f'opname_diff:{p_op}->{s_op}'
    # opname 相同，argval 不同
    p_arg = pyc_instr[2]
    s_arg = src_instr[2]
    if p_op.startswith('LOAD_CONST'):
        return 'const_value_diff'
    if p_op.startswith(('LOAD', 'STORE')):
        return f'argval_diff:{p_op}'
    if 'JUMP' in p_op:
        return 'jump_target_diff'
    return f'argval_diff:{p_op}'


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    if src_codes is None:
        return

    common = set(pyc_codes.keys()) & set(src_codes.keys())
    pattern_counter = Counter()
    func_patterns = []

    for name in sorted(common):
        pc = pyc_codes[name]
        sc = src_codes[name]
        if code_normalize(pc) == code_normalize(sc):
            continue
        if code_normalize_instr_only(pc) == code_normalize_instr_only(sc):
            func_patterns.append((name, 'sig_diff_only', None, None))
            pattern_counter['sig_diff_only'] += 1
            continue
        diff = find_first_diff(pc, sc)
        if diff is None:
            func_patterns.append((name, 'unknown', None, None))
            pattern_counter['unknown'] += 1
            continue
        idx, pi, si, pctx, sctx = diff
        pattern = classify_diff(pi, si, pctx, sctx)
        pattern_counter[pattern] += 1
        func_patterns.append((name, pattern, (pi, si), (pctx, sctx)))

    print(f"\n=== R13 失败模式汇总 ===")
    print(f"总失败函数: {len(func_patterns)}")
    print(f"\n--- 模式分布 ---")
    for pat, cnt in pattern_counter.most_common():
        print(f"  {cnt:3d}  {pat}")

    print(f"\n--- 每个函数的首个差异 (前40) ---")
    for name, pattern, diff_pair, ctx in func_patterns[:40]:
        print(f"\n  [{pattern}] {name}")
        if diff_pair is None:
            continue
        pi, si = diff_pair
        pctx, sctx = ctx
        print(f"    pyc: {pi}")
        print(f"    src: {si}")
        if pctx:
            print(f"    pyc ctx:")
            for c in pctx:
                print(f"      {c}")
        if sctx:
            print(f"    src ctx:")
            for c in sctx:
                print(f"      {c}")


if __name__ == '__main__':
    main()
