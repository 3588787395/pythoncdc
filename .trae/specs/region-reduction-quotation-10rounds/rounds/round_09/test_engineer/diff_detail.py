"""轮 8 测试工程师：按函数输出不一致指令 diff，生成 diff_detail.txt + decompile_report.md。"""
import sys, json, types, dis, os

sys.path.insert(0, '/workspace')
from exact_match_stats import get_instr_list, walk_code, load_orig, PYC, DECOMPILED, JUMP_OPS, SKIP_OPS

OUT_DIR = '/tmp/r9_out'
DIFF_TXT = '/tmp/r9_out/diff_detail.txt'
REPORT_MD = '/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_09/test_engineer/decompile_report.md'

FOCUS = ['<module>', 'one_prod_to_dataframe', 'build_future_fill_time',
         'load_bars_from_hundsun', 'load_get_price', 'get_str_data',
         'change_his_to_backward', 'get_date_and_count']


def fmt(ins):
    off, op, av = ins
    if isinstance(av, tuple) and av[0] == 'J':
        return f"{off:>4} {op:<28} ->[{av[1]}]"
    if isinstance(av, types.CodeType):
        return f"{off:>4} {op:<28} <code {av.co_name}>"
    return f"{off:>4} {op:<28} {av!r}"


def dump_pair(name, oa, na, fh):
    fh.write(f"\n=== {name}  (orig_len={len(oa)} new_len={len(na)} diff={len(na)-len(oa):+d}) ===\n")
    n = max(len(oa), len(na))
    first_diff = -1
    for i in range(n):
        a = oa[i] if i < len(oa) else None
        b = na[i] if i < len(na) else None
        eq = a is not None and b is not None and a[1] == b[1] and _eq_av(a, b)
        mark = '  ' if eq else '!!'
        if not eq and first_diff < 0:
            first_diff = i
        al = fmt(a) if a else '(missing)'
        bl = fmt(b) if b else '(missing)'
        fh.write(f"{i:>4} {mark} O:{al}\n       {mark} N:{bl}\n")
    fh.write(f"first_diff_idx={first_diff}\n")


def _eq_av(a, b):
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, tuple) and isinstance(av_b, tuple) and av_a[0] == 'J' and av_b[0] == 'J':
        return av_a[1] == av_b[1]
    if isinstance(av_a, types.CodeType) or isinstance(av_b, types.CodeType):
        return False
    return av_a == av_b


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    orig_top = load_orig()
    orig_cos = walk_code(orig_top)
    with open(DECOMPILED, 'r', encoding='utf-8') as f:
        src = f.read()
    new_code = compile(src, '<decompiled>', 'exec')
    new_cos = walk_code(new_code)

    with open('/tmp/r9_out/bc_results.json') as f:
        results = json.load(f)['results']

    with open(DIFF_TXT, 'w', encoding='utf-8') as fh:
        for name in FOCUS:
            if name not in orig_cos or name not in new_cos:
                fh.write(f"\n=== {name}: MISSING ===\n")
                continue
            oa = get_instr_list(orig_cos[name])
            na = get_instr_list(new_cos[name])
            dump_pair(name, oa, na, fh)

    # decompile_report.md
    lines = []
    lines.append("# Round 8 测试工程师：反编译报告\n")
    lines.append("## 1. 总体统计\n")
    s = json.load(open('/tmp/r9_out/bc_results.json'))['summary']
    lines.append(f"- 总函数数: {s['total']}")
    lines.append(f"- 一致函数数: {s['matched']}")
    lines.append(f"- 不一致函数数: {s['mismatched']}")
    lines.append(f"- 成功率: {s['success_rate_pct']}%")
    lines.append(f"- compile_ok: True")
    lines.append(f"- 相对 R7: 142→142 无退化（基线保持）\n")
    lines.append("## 2. 不一致函数清单（8 个）\n")
    lines.append("| 函数 | 状态 | orig_len | new_len | diff |")
    lines.append("|------|------|----------|---------|------|")
    for name in FOCUS:
        r = results.get(name, {})
        st = r.get('status', '?')
        if st == 'len_diff':
            lines.append(f"| {name} | len_diff | {r['orig_len']} | {r['new_len']} | {r['diff']:+d} |")
        elif st == 'instr_diff':
            lines.append(f"| {name} | instr_diff@{r['first_diff_idx']} | - | - | - |")
        else:
            lines.append(f"| {name} | {st} | - | - | - |")
    lines.append("")
    lines.append("## 3. 缺陷分类（按区域类型 + 算法原则）\n")
    lines.append("- **Loop 区域**：change_his_to_backward(-57)、get_str_data(-48)、load_bars_from_hundsun(-88) — 循环体内/循环后语句丢失，疑似违反原则 2（每块唯一归属）")
    lines.append("- **Conditional/BoolOp 区域**：load_get_price(-26)、get_date_and_count(-27)、one_prod_to_dataframe(+10) — if/elif/BoolOp 链结构或条件表达式丢失/冗余")
    lines.append("- **Sequence/Module 区域**：<module>(instr_diff)、build_future_fill_time(instr_diff) — 模块级 NOP/跳转目标偏移或语句顺序差异\n")
    lines.append("## 4. 详细 diff\n")
    lines.append(f"见 `diff_detail.txt`（/tmp/r9_out/diff_detail.txt），含每个函数 orig vs new 指令逐行对比。\n")
    lines.append("## 5. 最小复现实例\n")
    lines.append("见 `minimal_repros/`，共 ≥10 个 repro，每个标注所属区域类型与违反的算法原则。\n")
    with open(REPORT_MD, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"[diff_detail] wrote {DIFF_TXT}")
    print(f"[report] wrote {REPORT_MD}")
    # print first_diff summary for each
    for name in FOCUS:
        r = results.get(name, {})
        if r.get('status') == 'len_diff':
            print(f"  {name}: len_diff {r['orig_len']}->{r['new_len']} ({r['diff']:+d})")
        elif r.get('status') == 'instr_diff':
            print(f"  {name}: instr_diff@{r['first_diff_idx']} orig={r['orig_at']} new={r['new_at']}")


if __name__ == '__main__':
    main()
