"""轮 1 测试工程师：按函数输出不一致指令 diff。

对 9 个不一致函数，输出 orig vs new 的完整指令 diff（带 offset/opname/argval），
写入 diff_detail.txt。重点标注每个函数第一处不一致位置及其上下文（前后 10 条指令），
用于后续根因定位。

比较策略：
  - 长度不等：用序列对齐找出首个发散区段，输出首处发散上下文 + 末尾发散上下文
  - 长度相等但某条不一致：定位 first_diff idx，输出 [idx-10, idx+10] 区间
"""
import sys
import json
import types
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r1_decompiled.py'
OUT_DIR = '/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_01/test_engineer'
OUT_TXT = OUT_DIR + '/diff_detail.txt'
BC_JSON = OUT_DIR + '/bc_results.json'

SKIP_OPS = ('EXTENDED_ARG', 'CACHE')
CONTEXT = 10

# 9 个不一致函数（与基线一致）
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
    lines.append("Round 1 测试工程师 — 9 个不一致函数指令 diff 详情")
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
        lo = max(0, idx - CONTEXT)
        hi = min(max(len(oa), len(na)), idx + CONTEXT + 1)
        lines.append(f"{'idx':>5} | {'ORIG':<60} | {'NEW':<60}")
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

    out = "\n".join(lines) + "\n"
    with open(OUT_TXT, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f"[diff_detail] wrote {OUT_TXT} ({len(out)} chars, {out.count(chr(10))} lines)")


if __name__ == '__main__':
    main()
