"""轮 5 测试工程师：按函数输出不一致指令 diff。

对 9 个不一致函数，输出 orig vs new 的完整指令 diff（带 offset/opname/argval），
写入 diff_detail.txt。

R5 重点：对 build_future_fill_time 输出完整 orig vs new 指令序列对照（671 条），
标注所有 JUMP_FORWARD/JUMP_BACKWARD 目标差异点，定位偏移 74 字节的确切指令对。
"""
import sys
import json
import types
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r5_decompiled.py'
OUT_DIR = '/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_05/test_engineer'
OUT_TXT = OUT_DIR + '/diff_detail.txt'
BC_JSON = OUT_DIR + '/bc_results.json'

SKIP_OPS = ('EXTENDED_ARG', 'CACHE')
CONTEXT = 10

# 9 个不一致函数
TARGET_FUNCS = [
    '<module>',
    'one_prod_to_dataframe',
    'fill_minute_or_day_blank',
    'build_future_fill_time',
    'load_bars_from_hundsun',
    'load_get_price',
    'get_str_data',
    'change_his_to_backward',
    'get_date_and_count',
]

JUMP_OPS = (
    'JUMP_FORWARD', 'JUMP_BACKWARD',
    'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
    'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
    'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
)


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


def walk_code(co: types.CodeType, prefix: str = '', sink: dict = None):
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


def find_first_diff(oa, na):
    """返回 (idx, orig_at, new_at) 或 None（全等）。"""
    n = min(len(oa), len(na))
    for i in range(n):
        a, b = oa[i], na[i]
        if a[1] != b[1]:
            return i, a, b
        av_a, av_b = a[2], b[2]
        if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
            sub = find_first_diff(get_instr_list(av_a), get_instr_list(av_b))
            if sub is not None:
                return i, a, b
        elif isinstance(av_a, types.CodeType) or isinstance(av_b, types.CodeType):
            return i, a, b
        elif av_a != av_b:
            return i, a, b
    if len(oa) != len(na):
        return n, oa[n] if n < len(oa) else None, na[n] if n < len(na) else None
    return None


def main() -> None:
    orig_top = load_orig_top()
    orig_cos = walk_code(orig_top)

    with open(DECOMPILED, 'r', encoding='utf-8') as f:
        src = f.read()
    new_code = compile(src, '<decompiled>', 'exec')
    new_cos = walk_code(new_code)

    with open(BC_JSON, 'r', encoding='utf-8') as f:
        bc = json.load(f)
    summary = bc['summary']
    results = bc['results']

    lines = []
    lines.append("=" * 80)
    lines.append("Round 5 测试工程师 — 9 个不一致函数指令 diff 详情")
    lines.append("=" * 80)
    lines.append(f"pyc: {PYC}")
    lines.append(f"decompiled: {DECOMPILED}")
    lines.append(f"compile_ok: {summary['compile_ok']}")
    lines.append(f"total={summary['total']} matched={summary['matched']} "
                 f"mismatched={summary['mismatched']} missing={summary['missing']} "
                 f"success_rate={summary['success_rate_pct']}%")
    lines.append("")
    lines.append("说明：")
    lines.append("  - 指令格式：offset opname argval")
    lines.append("  - 跳过 EXTENDED_ARG / CACHE")
    lines.append("  - code object 类型 argval 显示 <code name len=N>")
    lines.append("  - 首处不一致位置标 [FIRST DIFF]，前后各展示 10 条上下文")
    lines.append("  - R5 重点定位 build_future_fill_time JUMP_FORWARD 2660→2586 (偏移 74 字节)")
    lines.append("    + one_prod_to_dataframe 尾部 spurious return (+11)")
    lines.append("")

    for fname in TARGET_FUNCS:
        r = results.get(fname, {})
        lines.append("=" * 80)
        lines.append(f"FUNCTION: {fname}")
        lines.append(f"STATUS: {r.get('status')}")
        if r.get('status') == 'len_diff':
            lines.append(f"orig_len={r['orig_len']} new_len={r['new_len']} diff={r['diff']:+d}")
        elif r.get('status') == 'instr_diff':
            lines.append(f"first_diff_idx={r['first_diff_idx']} orig_at={r['orig_at']} new_at={r['new_at']}")
        lines.append("-" * 80)

        if fname not in orig_cos:
            lines.append("[MISSING in orig]")
            continue
        if fname not in new_cos:
            lines.append("[MISSING in new]")
            continue

        oa = get_instr_list(orig_cos[fname])
        na = get_instr_list(new_cos[fname])
        lines.append(f"orig instructions: {len(oa)}")
        lines.append(f"new  instructions: {len(na)}")

        diff = find_first_diff(oa, na)
        if diff is None:
            lines.append("[no diff found — top-level equal]")
            continue
        idx, oa_ins, na_ins = diff
        lines.append("")
        lines.append(f"--- FIRST DIFF @ idx={idx} ---")
        lines.append(f"  ORIG: {instr_repr(oa_ins) if oa_ins else '<end>'}")
        lines.append(f"  NEW : {instr_repr(na_ins) if na_ins else '<end>'}")
        lines.append("")
        lines.append(f"--- CONTEXT [idx-{CONTEXT}, idx+{CONTEXT}] ---")
        lines.append(f"{'idx':>5} | {'ORIG':<60} | {'NEW':<60}")
        lo = max(0, idx - CONTEXT)
        hi = min(max(len(oa), len(na)), idx + CONTEXT + 1)
        for i in range(lo, hi):
            o_part = instr_repr(oa[i]) if i < len(oa) else '<end>'
            n_part = instr_repr(na[i]) if i < len(na) else '<end>'
            marker = ">>" if i == idx else "  "
            lines.append(f"{i:>5} {marker} {o_part:<60} | {n_part:<60}")
        lines.append("")

        # 末尾发散（长度不等时）
        if len(oa) != len(na):
            common = min(len(oa), len(na))
            tail_start = max(0, common - 5)
            lines.append(f"--- TAIL DIVERGE (common_prefix_len={common}) ---")
            lines.append(f"{'idx':>5} | {'ORIG':<60} | {'NEW':<60}")
            for i in range(tail_start, max(len(oa), len(na))):
                o_part = instr_repr(oa[i]) if i < len(oa) else '<end>'
                n_part = instr_repr(na[i]) if i < len(na) else '<end>'
                lines.append(f"{i:>5}    {o_part:<60} | {n_part:<60}")
            lines.append("")

        # 若是 instr_diff 且首处是 code object argval，递归展示子 code 的 diff
        if r.get('status') == 'instr_diff' and idx < min(len(oa), len(na)):
            a = oa[idx]
            b = na[idx]
            if isinstance(a[2], types.CodeType) and isinstance(b[2], types.CodeType):
                sub_oa = get_instr_list(a[2])
                sub_na = get_instr_list(b[2])
                lines.append(f"--- SUB-CODE DIFF for argval code '{a[2].co_name}' "
                             f"(orig_len={len(sub_oa)}, new_len={len(sub_na)}) ---")
                sub_diff = find_first_diff(sub_oa, sub_na)
                if sub_diff is not None:
                    sidx, sa, sb = sub_diff
                    lines.append(f"  sub first_diff @ idx={sidx}")
                    lines.append(f"    ORIG: {instr_repr(sa) if sa else '<end>'}")
                    lines.append(f"    NEW : {instr_repr(sb) if sb else '<end>'}")
                    slo = max(0, sidx - CONTEXT)
                    shi = min(max(len(sub_oa), len(sub_na)), sidx + CONTEXT + 1)
                    for i in range(slo, shi):
                        o_part = instr_repr(sub_oa[i]) if i < len(sub_oa) else '<end>'
                        n_part = instr_repr(sub_na[i]) if i < len(sub_na) else '<end>'
                        marker = ">>" if i == sidx else "  "
                        lines.append(f"  {i:>5} {marker} {o_part:<60} | {n_part:<60}")
                else:
                    lines.append("  sub-code top-level equal")
                lines.append("")

        # ===== R5 特殊：对 build_future_fill_time 输出完整指令序列对照 + 跳转差异 =====
        if fname == 'build_future_fill_time':
            lines.append("=" * 80)
            lines.append("### build_future_fill_time 完整指令对照（671 条）与跳转差异标注 ###")
            lines.append("=" * 80)
            n = min(len(oa), len(na))
            lines.append(f"共 {n} 条指令对照（orig_len={len(oa)}, new_len={len(na)}）")
            lines.append("")
            # 收集所有差异点
            diff_points = []
            for i in range(n):
                a = oa[i]
                b = na[i]
                if a[1] != b[1] or a[2] != b[2]:
                    diff_points.append(i)
            lines.append(f"差异点总数: {len(diff_points)}")
            lines.append("")
            lines.append("--- 所有差异点（含跳转目标差异）---")
            for i in diff_points:
                a = oa[i]
                b = na[i]
                is_jump = a[1] in JUMP_OPS or b[1] in JUMP_OPS
                tag = " [JUMP]" if is_jump else ""
                lines.append(f"  idx={i:4d}{tag}")
                lines.append(f"    ORIG: {instr_repr(a)}")
                lines.append(f"    NEW : {instr_repr(b)}")
                # 若是 JUMP_FORWARD，计算偏移差
                if a[1] == 'JUMP_FORWARD' and b[1] == 'JUMP_FORWARD':
                    off_a = a[2] if isinstance(a[2], int) else None
                    off_b = b[2] if isinstance(b[2], int) else None
                    if off_a is not None and off_b is not None:
                        delta = off_a - off_b
                        lines.append(f"    JUMP_FORWARD 目标偏移差: orig-new = {delta} 字节"
                                     f" ({delta} / 2 = {delta/2} 条指令)")
            lines.append("")
            # 计算每个 JUMP_FORWARD 差异点对应的目标块
            lines.append("--- JUMP_FORWARD 差异点目标块分析 ---")
            # 建 offset -> idx 映射
            off_to_idx_orig = {ins[0]: i for i, ins in enumerate(oa)}
            off_to_idx_new = {ins[0]: i for i, ins in enumerate(na)}
            for i in diff_points:
                a = oa[i]
                b = na[i]
                if a[1] != 'JUMP_FORWARD' or b[1] != 'JUMP_FORWARD':
                    continue
                if not (isinstance(a[2], int) and isinstance(b[2], int)):
                    continue
                tgt_o = a[2]
                tgt_n = b[2]
                lines.append(f"  JUMP_FORWARD @ orig_offset={a[0]} (idx={i}):")
                lines.append(f"    ORIG 目标 offset={tgt_o}")
                lines.append(f"    NEW  目标 offset={tgt_n}")
                lines.append(f"    偏移差={tgt_o - tgt_n} 字节")
                # orig 目标处的指令
                if tgt_o in off_to_idx_orig:
                    tidx = off_to_idx_orig[tgt_o]
                    lines.append(f"    ORIG 目标处指令 (idx={tidx}): {instr_repr(oa[tidx])}")
                else:
                    lines.append(f"    ORIG 目标 offset={tgt_o} 不在 orig 指令边界（可能落在 EXTENDED_ARG/对齐）")
                if tgt_n in off_to_idx_new:
                    tidx = off_to_idx_new[tgt_n]
                    lines.append(f"    NEW  目标处指令 (idx={tidx}): {instr_repr(na[tidx])}")
                else:
                    lines.append(f"    NEW  目标 offset={tgt_n} 不在 new 指令边界（可能落在 EXTENDED_ARG/对齐）")
            lines.append("")

    out = "\n".join(lines) + "\n"
    with open(OUT_TXT, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f"[diff_detail] wrote {OUT_TXT} ({len(out)} chars, {out.count(chr(10))} lines)")


if __name__ == '__main__':
    main()
