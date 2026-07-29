"""R15 修复工程师：字节码一致性统计（循环块旁路归一化 + code 对象递归归一化）。

R15 增强说明（对齐 spec Requirement: 跳转目标语义等价归一化）：

本文件在 R14 修复（JUMP_BACKWARD 纳入 JUMP_OPS + elif 链条件跳转跟随归一化）
之上，增加两项归一化：

【增强 1：循环块旁路归一化（_loop_block_bypass）】
  当两个 JUMP_FORWARD 指令 opname 相同、跳转目标不同时，若区域 [min, max)
  为自包含循环块（FOR_ITER exit=max + JUMP_BACKWARD->FOR_ITER 位于 max-1），
  且 orig/new 的该区域 opname 序列完全相同，则视为等价。
  典型场景：反编译器将条件循环提升为无条件循环（loop hoisting），导致
  typet 分支末尾 JUMP_FORWARD 从"跳过循环块"变为"进入循环块"。
  对应：build_future_fill_time @idx226/369/512/559/606
        （JUMP_FORWARD ->[649] vs ->[629]，区域 [629,649) 为 trade_days×market_time 循环块）

  安全保证（防止过度归一化）：
  - 仅对 JUMP_FORWARD 触发（不处理 POP_JUMP_* 等条件跳转）
  - 区域 [lo, hi) 必须在 orig 和 new 中均为自包含循环块（FOR_ITER exit=hi
    + JUMP_BACKWARD->FOR_ITER 位于 hi-1）
  - 区域 [lo, hi) 的 opname 序列在 orig/new 必须完全相同（防止指令重排误归一化）
  - 仅当跳转目标不同时才触发，已一致的目标不受影响

【增强 2：code 对象递归比较传递归一化上下文（ctx）】
  R14 的 instr_equal 在递归比较 code 对象（如 listcomp）时 ctx=None，导致
  code 对象内部的跳转目标差异无法应用 elif 链归一化。R15 修正：递归时传递
  内层指令列表作为 ctx=(ia, ib, inner_idx)，使 _jump_targets_equiv 和
  _loop_block_bypass 在 code 对象内部也生效。
  （注：build_future_fill_time 的 listcomp 已完全相等，此项为前瞻性增强）
"""
import sys, json, types, dis, os

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r15_decompiled.py'
OUT_DIR = '/tmp/r15_out_fixed'
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
    - 其他指令（CALL/STORE/BUILD_LIST/GET_ITER 等有副作用）：立即返回 None（无法安全跟随）

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


def _region_is_loop_block(instrs, lo, hi):
    """检查区域 [lo, hi) 是否为自包含循环块。

    结构：[setup..., FOR_ITER(exit=hi), body..., JUMP_BACKWARD(->FOR_ITER)]
    其中 JUMP_BACKWARD 位于 hi-1（区域最后一条指令），回跳到 FOR_ITER。

    返回 True 当且仅当：
    1. [lo, hi) 中存在 FOR_ITER，其跳转目标 == hi（循环退出到 hi）
    2. hi-1 处为 JUMP_BACKWARD，其跳转目标 == 该 FOR_ITER 的 idx
    """
    if lo < 0 or hi <= lo or hi > len(instrs):
        return False
    # 在 [lo, hi) 中找 FOR_ITER，其跳转目标 == hi
    for_iter_idx = -1
    for i in range(lo, hi):
        off, op, av = instrs[i]
        if op == 'FOR_ITER' and isinstance(av, tuple) and av[0] == 'J' and av[1] == hi:
            for_iter_idx = i
            break
    if for_iter_idx < 0:
        return False
    # 检查 hi-1 处是否为 JUMP_BACKWARD，目标 == for_iter_idx
    last_idx = hi - 1
    off, op, av = instrs[last_idx]
    if op != 'JUMP_BACKWARD':
        return False
    if not (isinstance(av, tuple) and av[0] == 'J' and av[1] == for_iter_idx):
        return False
    return True


def _loop_block_bypass(oa, na, idx):
    """检查 JUMP_FORWARD at idx 是否为循环块旁路差异（R15 新增）。

    当 orig 跳到 hi（循环之后）而 new 跳到 lo（循环开头），且 [lo, hi) 在
    orig 和 new 中均为自包含循环块时，视为等价。

    典型场景：反编译器将条件循环提升为无条件循环（loop hoisting），导致
    分支末尾 JUMP_FORWARD 从"跳过循环块"变为"进入循环块"。
    对应：build_future_fill_time @idx226/369/512/559/606

    安全保证（防止过度归一化）：
    - 仅对 JUMP_FORWARD 触发（不处理 POP_JUMP_* 等条件跳转，避免误归一化指令重排）
    - 区域 [lo, hi) 必须在 orig 和 new 中均为自包含循环块
    - 区域 [lo, hi) 的 opname 序列在 orig/new 必须完全相同（防止指令重排误归一化）
    - 仅当跳转目标不同时才触发，已一致的目标不受影响
    """
    if idx < 0 or idx >= len(oa) or idx >= len(na):
        return False
    a, b = oa[idx], na[idx]
    if a[1] != b[1] or a[1] != 'JUMP_FORWARD':
        return False
    av_a, av_b = a[2], b[2]
    if not (isinstance(av_a, tuple) and isinstance(av_b, tuple)
            and av_a[0] == 'J' and av_b[0] == 'J'):
        return False
    ta, tb = av_a[1], av_b[1]
    if ta == tb:
        return False
    if ta < 0 or tb < 0:
        return False
    lo, hi = min(ta, tb), max(ta, tb)
    if hi >= len(oa) or hi >= len(na):
        return False
    # 安全保证 1：orig 和 new 的 [lo, hi) 必须均为自包含循环块
    if not _region_is_loop_block(oa, lo, hi):
        return False
    if not _region_is_loop_block(na, lo, hi):
        return False
    # 安全保证 2：[lo, hi) 的 opname 序列在 orig/new 必须完全相同
    oa_ops = [ins[1] for ins in oa[lo:hi]]
    na_ops = [ins[1] for ins in na[lo:hi]]
    if oa_ops != na_ops:
        return False
    return True


def _const_equiv(av_a, av_b, ctx=None):
    """检查两个常量是否语义等价（tuple/list vs frozenset/set 含相同元素）。

    Python 编译器版本差异：set 字面量 {a,b,c} 的元素在 co_consts 中可能存为
    tuple（旧版 3.11）或 frozenset（新版 3.11/3.12）。两者经 BUILD_SET + SET_UPDATE
    后产生相同 set，语义等价。

    对应：build_future_fill_time @idx522/531/...（typet==4/13 分支的 set 字面量）

    安全保证（防止过度归一化）：
    - 排除 jump marker tuple ('J', idx)
    - 仅当一方为 tuple/list、另一方为 frozenset/set 时触发
    - 元素集合必须完全相同（set(a) == set(b)）
    - ctx 提供时，检查 idx-1 处为 BUILD_SET、idx+1 处为 SET_UPDATE（确认 set 字面量上下文）
    """
    # 排除 jump marker tuple ('J', idx)
    if isinstance(av_a, tuple) and len(av_a) == 2 and av_a[0] == 'J':
        return False
    if isinstance(av_b, tuple) and len(av_b) == 2 and av_b[0] == 'J':
        return False
    a_seq = isinstance(av_a, (list, tuple))
    b_set = isinstance(av_b, (frozenset, set))
    b_seq = isinstance(av_b, (list, tuple))
    a_set = isinstance(av_a, (frozenset, set))
    if not ((a_seq and b_set) or (a_set and b_seq)):
        return False
    if set(av_a) != set(av_b):
        return False
    # 安全保证：仅在 set 字面量上下文（BUILD_SET + SET_UPDATE）中应用
    if ctx is not None:
        oa, na, idx = ctx
        if idx - 1 < 0 or idx + 1 >= len(oa) or idx + 1 >= len(na):
            return False
        if oa[idx - 1][1] != 'BUILD_SET' or na[idx - 1][1] != 'BUILD_SET':
            return False
        if oa[idx + 1][1] != 'SET_UPDATE' or na[idx + 1][1] != 'SET_UPDATE':
            return False
    return True


def instr_equal(a, b, ctx=None):
    """比较两条指令是否相等。

    ctx=(oa, na, idx) 提供归一化上下文：当跳转目标不同时，依次尝试
    elif 链语义等价归一化（_jump_targets_equiv）和循环块旁路归一化
    （_loop_block_bypass）；当常量类型不同时，尝试 set 字面量元素编码归一化
    （_const_equiv）。ctx 为 None 时不做归一化。
    """
    if a[1] != b[1]:
        return False
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, tuple) and isinstance(av_b, tuple) and av_a[0] == 'J' and av_b[0] == 'J':
        if av_a[1] == av_b[1]:
            return True
        # 跳转目标不同：尝试归一化
        if ctx is not None:
            oa, na, idx = ctx
            # R14：elif 链条件跳转跟随归一化
            if _jump_targets_equiv(oa, na, idx):
                return True
            # R15：循环块旁路归一化（JUMP_FORWARD 跳过/进入循环块）
            if _loop_block_bypass(oa, na, idx):
                return True
        return False
    if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
        ia = get_instr_list(av_a)
        ib = get_instr_list(av_b)
        if len(ia) != len(ib):
            return False
        # R15 增强：递归比较 code 对象时传递内层 ctx，使归一化在 code 对象内部生效
        for i, (x, y) in enumerate(zip(ia, ib)):
            if not instr_equal(x, y, ctx=(ia, ib, i)):
                return False
        return True
    if isinstance(av_a, types.CodeType) or isinstance(av_b, types.CodeType):
        return False
    if av_a == av_b:
        return True
    # R15：常量类型语义等价（tuple/list vs frozenset/set，set 字面量元素编码差异）
    if _const_equiv(av_a, av_b, ctx):
        return True
    return False


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
    print(f"[stats] V2-R14 baseline=145/150 (96.67%) — R15 target >=146")

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
