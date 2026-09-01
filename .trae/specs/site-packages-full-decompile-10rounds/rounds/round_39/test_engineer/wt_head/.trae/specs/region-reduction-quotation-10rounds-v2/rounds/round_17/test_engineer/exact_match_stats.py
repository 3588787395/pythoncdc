"""R17 测试工程师：字节码一致性统计（继承 R16 归一化逻辑，建立基线）。

归一化说明（继承 R14/R15/R16）：
- SKIP_OPS 过滤掉 EXTENDED_ARG/CACHE/NOP 等无语义指令。
- JUMP_OPS 的 argval 由字节码 offset 归一化为过滤后的指令索引（含 JUMP_BACKWARD）。
- elif 链条件跳转跟随归一化（R14）：当两个跳转指令 opname 相同、目标 idx 不同时，
  从较小目标出发跟随条件跳转链，若能到达较大目标则视为语义等价。
- 循环块旁路归一化（R15）：JUMP_FORWARD 跳过/进入后置循环块的目标偏移归一化。
- set 字面量常量编码归一化（R15）：tuple/list vs frozenset/set 元素集合等价。
- code 对象递归比较传递 ctx（R15）：使归一化在 listcomp 等 code 对象内部生效。
- code 对象 co_filename 元数据归一化（R16）：显式忽略 co_filename/co_firstlineno，
  保留 co_name 比较，递归比较字节码指令序列。

R17 基线（与 R16 修复后一致）= 146/150 (97.33%)，残留 4 个不一致函数：
- <module>: 传递性不一致（R17 重点）— 通过 LOAD_CONST <code get_str_data> 嵌入了
  自身不一致的 code 对象（get_str_data len_diff -48），递归比较时失败。
- get_str_data: len_diff -48（R12 遗留）
- change_his_to_backward: instr_diff@296（R14 defer，指令重排）
- get_date_and_count: len_diff -27（R13 遗留）

R17 重点：解决 <module> 的传递性不一致 — 嵌套 code 对象已作为独立函数比较过，
<module> 不应重复比较其内部。修复工程师阶段将引入"传递性不一致委托"机制。
"""
import sys, json, types, dis, os

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r17_decompiled.py'
OUT_DIR = '/tmp/r17_out'
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
    """从 start_idx 跟随 elif 链条件跳转 false 分支，尝试到达 >= ceiling 的位置。"""
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
        if op in COND_JUMP_OPS and isinstance(av, tuple) and av[0] == 'J':
            jt = av[1]
            if jt < 0:
                return None
            cur = jt
            continue
        if op == 'JUMP_FORWARD' and isinstance(av, tuple) and av[0] == 'J':
            jt = av[1]
            return jt if jt >= 0 else None
        if op in PURE_COND_OPS:
            cur = cur + 1
            continue
        return None
    return None


def _jump_targets_equiv(oa, na, idx):
    """检查 idx 处的跳转指令目标是否语义等价（elif 链归一化）。"""
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
    if _chase_elif_chain(oa, lo, hi) == hi:
        return True
    if _chase_elif_chain(na, lo, hi) == hi:
        return True
    return False


def _region_is_loop_block(instrs, lo, hi):
    """检查区域 [lo, hi) 是否为自包含循环块。"""
    if lo < 0 or hi <= lo or hi > len(instrs):
        return False
    for_iter_idx = -1
    for i in range(lo, hi):
        off, op, av = instrs[i]
        if op == 'FOR_ITER' and isinstance(av, tuple) and av[0] == 'J' and av[1] == hi:
            for_iter_idx = i
            break
    if for_iter_idx < 0:
        return False
    last_idx = hi - 1
    off, op, av = instrs[last_idx]
    if op != 'JUMP_BACKWARD':
        return False
    if not (isinstance(av, tuple) and av[0] == 'J' and av[1] == for_iter_idx):
        return False
    return True


def _loop_block_bypass(oa, na, idx):
    """检查 JUMP_FORWARD at idx 是否为循环块旁路差异（R15 继承）。"""
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
    if not _region_is_loop_block(oa, lo, hi):
        return False
    if not _region_is_loop_block(na, lo, hi):
        return False
    oa_ops = [ins[1] for ins in oa[lo:hi]]
    na_ops = [ins[1] for ins in na[lo:hi]]
    if oa_ops != na_ops:
        return False
    return True


def _const_equiv(av_a, av_b, ctx=None):
    """检查两个常量是否语义等价（tuple/list vs frozenset/set 含相同元素，R15 继承）。"""
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
    if ctx is not None:
        oa, na, idx = ctx
        if idx - 1 < 0 or idx + 1 >= len(oa) or idx + 1 >= len(na):
            return False
        if oa[idx - 1][1] != 'BUILD_SET' or na[idx - 1][1] != 'BUILD_SET':
            return False
        if oa[idx + 1][1] != 'SET_UPDATE' or na[idx + 1][1] != 'SET_UPDATE':
            return False
    return True


def _code_instr_equiv(av_a, av_b):
    """比较两个 code 对象是否字节码语义等价（R16：co_filename 归一化显式化）。

    归一化规则（文档化）：
    - 忽略 co_filename 差异（原始源文件路径 vs 反编译产物 '<decompiled>'）
    - 忽略 co_firstlineno 等纯位置元数据
    - 保留 co_name 比较（语义标识）
    - 递归比较字节码指令序列
    """
    if av_a.co_name != av_b.co_name:
        return False
    ia = get_instr_list(av_a)
    ib = get_instr_list(av_b)
    if len(ia) != len(ib):
        return False
    for i, (x, y) in enumerate(zip(ia, ib)):
        if not instr_equal(x, y, ctx=(ia, ib, i)):
            return False
    return True


def instr_equal(a, b, ctx=None):
    """比较两条指令是否相等（继承 R16 全部归一化）。"""
    if a[1] != b[1]:
        return False
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, tuple) and isinstance(av_b, tuple) and av_a[0] == 'J' and av_b[0] == 'J':
        if av_a[1] == av_b[1]:
            return True
        if ctx is not None:
            oa, na, idx = ctx
            if _jump_targets_equiv(oa, na, idx):
                return True
            if _loop_block_bypass(oa, na, idx):
                return True
        return False
    if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
        return _code_instr_equiv(av_a, av_b)
    if isinstance(av_a, types.CodeType) or isinstance(av_b, types.CodeType):
        return False
    if av_a == av_b:
        return True
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
    print(f"[stats] V2-R16 baseline=146/150 (97.33%) — R17 must not regress")

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
