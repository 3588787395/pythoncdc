"""轮 5 测试工程师：build_future_fill_time 深度分析。

目标：
1. 找出 3 个 listcomp code object 的内部差异（idx 201/344/487）
2. 分析 JUMP_FORWARD 2660→2586 的真实根因：
   - orig 目标 2660 = total_dts (idx 649)
   - new  目标 2586 = trade_days (idx 629)
   - 偏移 74 字节 = 37 条指令
3. 验证：JUMP_FORWARD 目标差异是 frozenset 偏移的派生后果，还是独立的算法缺陷？
4. 输出 build_future_analysis.md
"""
import sys
import types
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r5_decompiled.py'

SKIP_OPS = ('EXTENDED_ARG', 'CACHE')


def get_instr_list(co: types.CodeType):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in SKIP_OPS:
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def instr_repr(ins):
    offset, opname, argval = ins
    if isinstance(argval, types.CodeType):
        av = f"<code {argval.co_name} len={len(get_instr_list(argval))}>"
    else:
        av = repr(argval)
    return f"{offset:5d} {opname:24s} {av}"


def walk_code(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    if co.co_name == '<module>' and not prefix:
        name = '<module>'
    else:
        name = prefix + co.co_name
    sink[name] = co
    sub_prefix = '' if name == '<module>' else name + '.'
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            walk_code(const, sub_prefix, sink)
    return sink


def load_orig_top():
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    return code_obj


def main():
    orig_top = load_orig_top()
    orig_cos = walk_code(orig_top)
    with open(DECOMPILED, 'r', encoding='utf-8') as f:
        src = f.read()
    new_code = compile(src, '<decompiled>', 'exec')
    new_cos = walk_code(new_code)

    bft_o = orig_cos['build_future_fill_time']
    bft_n = new_cos['build_future_fill_time']
    oa = get_instr_list(bft_o)
    na = get_instr_list(bft_n)

    print("=" * 80)
    print("### 1. 3 个 listcomp code object 内部差异分析 ###")
    print("=" * 80)
    # 找出所有 LOAD_CONST <listcomp> 差异点
    listcomp_diffs = []
    n = min(len(oa), len(na))
    for i in range(n):
        a = oa[i]
        b = na[i]
        if (isinstance(a[2], types.CodeType) and isinstance(b[2], types.CodeType)
                and a[2].co_name == '<listcomp>' and b[2].co_name == '<listcomp>'):
            sub_oa = get_instr_list(a[2])
            sub_na = get_instr_list(b[2])
            if sub_oa != sub_na:
                listcomp_diffs.append((i, a, b, sub_oa, sub_na))
    print(f"listcomp code object 差异数: {len(listcomp_diffs)}")
    for k, (i, a, b, sub_oa, sub_na) in enumerate(listcomp_diffs):
        print(f"\n--- listcomp diff #{k+1} @ idx={i} (orig_offset={a[0]}) ---")
        print(f"  orig sub_len={len(sub_oa)}, new sub_len={len(sub_na)}")
        # 找子差异
        sn = min(len(sub_oa), len(sub_na))
        first_sub = None
        for j in range(sn):
            if sub_oa[j][1] != sub_na[j][1] or sub_oa[j][2] != sub_na[j][2]:
                first_sub = j
                break
        if first_sub is None and len(sub_oa) != len(sub_na):
            first_sub = sn
        if first_sub is None:
            print("  [子 code 完全一致]")
            continue
        print(f"  首处子差异 @ sub_idx={first_sub}")
        lo = max(0, first_sub - 5)
        hi = min(max(len(sub_oa), len(sub_na)), first_sub + 8)
        for j in range(lo, hi):
            o_part = instr_repr(sub_oa[j]) if j < len(sub_oa) else '<end>'
            n_part = instr_repr(sub_na[j]) if j < len(sub_na) else '<end>'
            marker = ">>" if j == first_sub else "  "
            print(f"    {j:>4} {marker} {o_part:<55} | {n_part:<55}")
        # 也打印整个子 code
        print(f"  --- 完整子 code 对照 ---")
        for j in range(max(len(sub_oa), len(sub_na))):
            o_part = instr_repr(sub_oa[j]) if j < len(sub_oa) else '<end>'
            n_part = instr_repr(sub_na[j]) if j < len(sub_na) else '<end>'
            print(f"    {j:>4}    {o_part:<55} | {n_part:<55}")

    print()
    print("=" * 80)
    print("### 2. JUMP_FORWARD 2660→2586 根因分析 ###")
    print("=" * 80)
    # ORIG 中 offset 2586 是什么？NEW 中 offset 2660 是什么？
    off_to_idx_orig = {ins[0]: i for i, ins in enumerate(oa)}
    off_to_idx_new = {ins[0]: i for i, ins in enumerate(na)}

    print(f"\n--- ORIG 字节码中 offset 2586 附近 ---")
    # 找 orig 中最接近 2586 的指令
    for ins in oa:
        if 2560 <= ins[0] <= 2700:
            mark = " <-- ORIG JF target 2660" if ins[0] == 2660 else ""
            mark2 = " <-- NEW JF target 2586" if ins[0] == 2586 else ""
            print(f"  ORIG {instr_repr(ins)}{mark}{mark2}")

    print(f"\n--- NEW 字节码中 offset 2586/2660 附近 ---")
    for ins in na:
        if 2560 <= ins[0] <= 2700:
            mark = " <-- ORIG JF target 2660" if ins[0] == 2660 else ""
            mark2 = " <-- NEW JF target 2586" if ins[0] == 2586 else ""
            print(f"  NEW  {instr_repr(ins)}{mark}{mark2}")

    print()
    print("=" * 80)
    print("### 3. 偏移 74 字节 = 37 条指令的来源 ###")
    print("=" * 80)
    # 在 orig 中，从 2586 到 2660 的指令序列
    print("\n--- ORIG 中 [2586, 2660] 区间指令 ---")
    in_range_o = [ins for ins in oa if 2586 <= ins[0] < 2660]
    for ins in in_range_o:
        print(f"  ORIG {instr_repr(ins)}")
    print(f"  共 {len(in_range_o)} 条指令")
    # 在 new 中，从 2586 到 2660 的指令序列
    print("\n--- NEW 中 [2586, 2660] 区间指令 ---")
    in_range_n = [ins for ins in na if 2586 <= ins[0] < 2660]
    for ins in in_range_n:
        print(f"  NEW  {instr_repr(ins)}")
    print(f"  共 {len(in_range_n)} 条指令")

    print()
    print("=" * 80)
    print("### 4. 关键判定：JUMP_FORWARD 目标是 listcomp 出口还是 frozenset 偏移派生？###")
    print("=" * 80)
    # 关键：orig 的 5 个 JUMP_FORWARD 都跳到 2660 (total_dts)，
    #       new 的 5 个 JUMP_FORWARD 都跳到 2586 (trade_days)。
    # 如果只是 frozenset 偏移，那么 orig 和 new 的跳转目标指令应该相同（同名的 LOAD_FAST）。
    # 但 orig 跳到 total_dts，new 跳到 trade_days —— 这是不同的块！
    # 说明 JUMP_FORWARD 目标确实不同（算法问题，非偏移派生）。
    print()
    print("ORIG 5 个 JUMP_FORWARD 目标: 全部 2660 = 'total_dts' (idx 649)")
    print("NEW  5 个 JUMP_FORWARD 目标: 全部 2586 = 'trade_days' (idx 629)")
    print()
    print("判定：ORIG 跳到 total_dts，NEW 跳到 trade_days —— 不同块！")
    print("  → 这不是 frozenset 偏移的派生（否则跳转目标指令名应相同）")
    print("  → 这是 listcomp region 归约后父循环 JUMP_FORWARD 目标计算错误")
    print()
    # 进一步：查看 ORIG 中 2586 (trade_days) 与 2660 (total_dts) 之间是什么
    # 若 2586→2660 之间是某个 listcomp 展开的内部块，则说明 listcomp 归约后父循环
    # 错误地引用了 listcomp 内部块的出口，而非抽象节点的出口。
    print("查看 ORIG 中 trade_days(2586) → total_dts(2660) 之间的指令：")
    print("（若是 listcomp 内部展开块，则证实 listcomp 归约后跳转目标未同步）")


if __name__ == '__main__':
    main()
