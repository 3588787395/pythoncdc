"""R15 测试工程师：字节码一致性统计（继承 R14 的跳转目标归一化逻辑）。

归一化说明（对齐 spec Requirement: 跳转目标语义等价归一化）：
- SKIP_OPS 过滤掉 EXTENDED_ARG/CACHE/NOP 等无语义指令。
- JUMP_OPS 的 argval 由字节码 offset 归一化为过滤后的指令索引（含 JUMP_BACKWARD）。
- elif 链条件跳转跟随归一化：当两个跳转指令 opname 相同、目标 idx 不同时，
  从较小目标出发跟随条件跳转链，若能到达较大目标则视为语义等价。

R15 基线：与 R14 修复后一致 = 145/150 (96.67%)，残留 5 个不一致函数：
- <module>: co_filename 元数据差异
- build_future_fill_time: instr_diff@226（R15 重点：listcomp code 对象 + 跳转目标偏移）
- get_str_data: len_diff -48（R12 遗留）
- change_his_to_backward: instr_diff@296（R14 defer，指令重排）
- get_date_and_count: len_diff -27（R13 遗留）

修复工程师阶段将在此文件上增强 listcomp code 对象跳转目标归一化（见 fix_report.md）。
"""
import sys, json, types, dis, os

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r15_decompiled.py'
OUT_DIR = '/tmp/r15_out'
OUT_JSON = OUT_DIR + '/bc_results.json'

SKIP_OPS = ('EXTENDED_ARG', 'CACHE', 'NOP')

# R14 修复：JUMP_BACKWARD 纳入 JUMP_OPS（使其 argval 经 offset_to_idx 映射为指令索引）
JUMP_OPS = frozenset({
    'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
    'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
    'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
    'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
    'POP_JUMP_IF_NONE', 'POP_JUMP_IF_NOT_NONE', 'POP_JUMP_FORWARD_IF_NONE',
    'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NONE',
    'POP_JUMP_BACKWARD_IF_NOT_NONE', 'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
    'JUMP_IF_NOT_EXC_MATCH', 'FOR_ITER',
})

# 条件跳转操作码（POP_JUMP_* 系列）：跳转目标为 false/none 分支
COND_JUMP_OPS = frozenset({
    'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
    'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
    'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
    'POP_JUMP_IF_NONE', 'POP_JUMP_IF_NOT_NONE',
    'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
    'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
})

# fall-forward 时允许的无副作用指令（纯条件检查，不改变程序状态）
PURE_COND_OPS = frozenset({
    'LOAD_FAST', 'LOAD_CONST', 'LOAD_GLOBAL', 'LOAD_NAME', 'LOAD_DEREF',
    'LOAD_ATTR', 'LOAD_METHOD', 'COMPARE_OP', 'IS_OP', 'CONTAINS_OP',
})


def get_instr_list(co):
    raw = [ins for ins in dis.get_instructions(co) if ins.opname not in SKIP_OPS]
    offset_to_idx = {ins.offset: idx for idx, ins in enumerate(raw)}
    instrs = []
    for idx, ins in enumerate(raw):
        if ins.opname in JUMP_OPS and ins.argval is not None and isinstance(ins.argval, int):
            target_idx = offset_to_idx.get(ins.argval, -1)
            instrs.append((ins.offset, ins.opname, ('J', target_idx)))
        else:
            instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def _chase_elif_chain(instrs, start_idx, ceiling):
    """从 start_idx 跟随 elif 链条件跳转 false 分支，尝试到达 >= ceiling 的位置。

    遍历规则（保守，防止过度归一化）：
    - 条件跳转 (POP_JUMP_IF_*)：跟随其跳转目标（false/none 分支），不进入 fall-through
    - JUMP_FORWARD：跟随其跳转目标（分支体末尾跳到链末尾）
    - PURE_COND_OPS (LOAD/COMPARE 等无副作用指令)：fall-forward 到下一条
    - 其他指令（CALL/STORE/BUILD_LIST 等有副作用）：立即返回 None（无法安全跟随）

    返回到达的指令 idx（>= ceiling），或 None 表示无法到达。
    """
    if start_idx < 0 or ceiling < 0 or start_idx >= len(instrs):
        return None
    visited = set()
    cur = start_idx
    steps = 0
    while 0 <= cur < len(instrs) and cur not in visited and steps < 200:
        visited.add(cur)
        steps += 1
        if cur >= ceiling:
            return cur
        ins = instrs[cur]
        op = ins[1]
        av = ins[2]
        # 条件跳转：跟随跳转目标（false/none 分支，即"跳过当前分支"）
        if op in COND_JUMP_OPS and isinstance(av, tuple) and av[0] == 'J':
            jt = av[1]
            if jt < 0:
                return None
            cur = jt
            continue
        # JUMP_FORWARD：跟随其跳转目标（分支体末尾跳到链末尾）
        if op == 'JUMP_FORWARD' and isinstance(av, tuple) and av[0] == 'J':
            jt = av[1]
            return jt if jt >= 0 else None
        # 无副作用条件检查指令：fall-forward
        if op in PURE_COND_OPS:
            cur = cur + 1
            continue
        # 有副作用或未知指令：停止，无法安全跟随
        return None
    return None


def _jump_targets_equiv(oa, na, idx):
    """检查 idx 处的跳转指令目标是否语义等价（elif 链归一化）。

    当两个跳转指令 opname 相同、目标 idx 不同时，从较小目标出发跟随条件跳转链，
    若能到达较大目标则视为语义等价。
    """
    if idx < 0 or idx >= len(oa) or idx >= len(na):
        return False
    a, b = oa[idx], na[idx]
    av_a, av_b = a[2], b[2]
    if not (isinstance(av_a, tuple) and isinstance(av_b, tuple)
            and av_a[0] == 'J' and av_b[0] == 'J'):
        return False
    ta, tb = av_a[1], av_b[1]
    if ta == tb:
        return True
    if ta < 0 or tb < 0:
        return False
    lo, hi = min(ta, tb), max(ta, tb)
    if lo >= len(oa) or hi >= len(oa):
        return False
    # 在 orig 指令列表中从 lo 跟随到 hi
    if _chase_elif_chain(oa, lo, hi) == hi:
        return True
    # 在 new 指令列表中从 lo 跟随到 hi
    if _chase_elif_chain(na, lo, hi) == hi:
        return True
    return False


def instr_equal(a, b, ctx=None):
    """比较两条指令是否相等。

    ctx=(oa, na, idx) 提供跳转目标归一化上下文：当跳转目标不同时，尝试 elif 链
    语义等价归一化。ctx 为 None（如嵌套 code object 递归比较）时不做归一化。
    """
    if a[1] != b[1]:
        return False
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, tuple) and isinstance(av_b, tuple) and av_a[0] == 'J' and av_b[0] == 'J':
        if av_a[1] == av_b[1]:
            return True
        # 跳转目标不同：尝试 elif 链语义等价归一化
        if ctx is not None:
            oa, na, idx = ctx
            if _jump_targets_equiv(oa, na, idx):
                return True
        return False
    if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
        ia = get_instr_list(av_a)
        ib = get_instr_list(av_b)
        if len(ia) != len(ib):
            return False
        return all(instr_equal(x, y) for x, y in zip(ia, ib))
    if isinstance(av_a, types.CodeType) or isinstance(av_b, types.CodeType):
        return False
    return av_a == av_b


def walk_code(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    name = '<module>' if (co.co_name == '<module>' and not prefix) else prefix + co.co_name
    sink[name] = co
    sub_prefix = '' if name == '<module>' else name + '.'
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            walk_code(const, sub_prefix, sink)
    return sink


def load_orig():
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    return code_obj


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    orig_top = load_orig()
    orig_cos = walk_code(orig_top)
    print(f"[stats] orig code objects: {len(orig_cos)}")

    with open(DECOMPILED, 'r', encoding='utf-8') as f:
        src = f.read()
    try:
        new_code = compile(src, '<decompiled>', 'exec')
        compile_ok = True
    except SyntaxError as e:
        new_code = None
        compile_ok = False
        print(f"[stats] compile FAILED: {e}")

    new_cos = walk_code(new_code) if new_code is not None else {}
    print(f"[stats] new code objects: {len(new_cos)}")

    results = {}
    matched = mismatched = missing = 0

    for name, orig_co in orig_cos.items():
        if name not in new_cos:
            results[name] = {'status': 'missing', 'orig_len': len(get_instr_list(orig_co))}
            missing += 1
            continue
        oa = get_instr_list(orig_co)
        na = get_instr_list(new_cos[name])
        if len(oa) != len(na):
            results[name] = {'status': 'len_diff', 'orig_len': len(oa), 'new_len': len(na), 'diff': len(na) - len(oa)}
            mismatched += 1
            continue
        first_diff = -1
        for i, (x, y) in enumerate(zip(oa, na)):
            if not instr_equal(x, y, ctx=(oa, na, i)):
                first_diff = i
                break
        if first_diff < 0:
            results[name] = {'status': 'match'}
            matched += 1
        else:
            results[name] = {'status': 'instr_diff', 'first_diff_idx': first_diff,
                             'orig_at': list(oa[first_diff]), 'new_at': list(na[first_diff])}
            mismatched += 1

    total = len(orig_cos)
    sr = matched / total * 100 if total else 0.0
    print(f"[stats] compile_ok={compile_ok}")
    print(f"[stats] total={total} matched={matched} mismatched={mismatched} missing={missing} success_rate={sr:.2f}%")
    print(f"[stats] V2-R14 baseline=145/150 (96.67%) — R15 must not regress")

    out = {'summary': {'total': total, 'matched': matched, 'mismatched': mismatched,
                       'missing': missing, 'success_rate_pct': round(sr, 2),
                       'compile_ok': compile_ok}, 'results': results}
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, default=str)
    print(f"[stats] wrote {OUT_JSON}")

    mism = [(n, r) for n, r in results.items() if r['status'] != 'match']
    print(f"[stats] mismatched functions ({len(mism)}):")
    for n, r in mism:
        if r['status'] == 'len_diff':
            print(f"  - {n}: len_diff orig={r['orig_len']} new={r['new_len']} (diff={r['diff']:+d})")
        elif r['status'] == 'instr_diff':
            print(f"  - {n}: instr_diff @idx{r['first_diff_idx']}")
        else:
            print(f"  - {n}: {r['status']}")


if __name__ == '__main__':
    main()
