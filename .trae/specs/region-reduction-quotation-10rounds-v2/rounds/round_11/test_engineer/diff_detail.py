"""R11 测试工程师：按函数输出不一致指令 diff，生成 diff_detail.txt + decompile_report.md。

FOCUS 为 V2 R11 的 7 个残留函数：
- load_get_price: Conditional+BoolOp 嵌套残留 -2 指令
- get_str_data: Loop 嵌套循环体语句丢失 -48
- get_date_and_count: Loop+Conditional while if/elif 链丢失 -27
- one_prod_to_dataframe / build_future_fill_time / change_his_to_backward: 跳转目标归一化差异
- <module>: co_filename 元数据差异
"""
import sys, json, types, dis, os

sys.path.insert(0, '/workspace')
from exact_match_stats import get_instr_list, walk_code, load_orig, PYC, DECOMPILED, OUT_DIR, JUMP_OPS, SKIP_OPS

DIFF_TXT = OUT_DIR + '/diff_detail.txt'
REPORT_MD = '/workspace/.trae/specs/region-reduction-quotation-10rounds-v2/rounds/round_11/test_engineer/decompile_report.md'

FOCUS = ['<module>', 'one_prod_to_dataframe', 'build_future_fill_time',
         'load_get_price', 'get_str_data', 'change_his_to_backward', 'get_date_and_count']


def fmt(ins):
    off, op, av = ins
    if isinstance(av, tuple) and av[0] == 'J':
        return f"{off:>4} {op:<28} ->[{av[1]}]"
    if isinstance(av, types.CodeType):
        return f"{off:>4} {op:<28} <code {av.co_name}>"
    return f"{off:>4} {op:<28} {av!r}"


def _eq_av(a, b):
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, tuple) and isinstance(av_b, tuple) and av_a[0] == 'J' and av_b[0] == 'J':
        return av_a[1] == av_b[1]
    if isinstance(av_a, types.CodeType) or isinstance(av_b, types.CodeType):
        return False
    return av_a == av_b


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


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    orig_top = load_orig()
    orig_cos = walk_code(orig_top)
    with open(DECOMPILED, 'r', encoding='utf-8') as f:
        src = f.read()
    new_code = compile(src, '<decompiled>', 'exec')
    new_cos = walk_code(new_code)

    with open(OUT_DIR + '/bc_results.json') as f:
        bc = json.load(f)
    results = bc['results']
    summary = bc['summary']

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
    lines.append("# R11 测试工程师：反编译报告\n")
    lines.append("## 1. 总体统计\n")
    lines.append(f"- 总函数数: {summary['total']}")
    lines.append(f"- 一致函数数: {summary['matched']}")
    lines.append(f"- 不一致函数数: {summary['mismatched']}")
    lines.append(f"- 成功率: {summary['success_rate_pct']}%")
    lines.append(f"- compile_ok: {summary.get('compile_ok', True)}")
    lines.append(f"- V1-R10 基线: 143/150 (95.33%) — R11 不得退化\n")
    lines.append("## 2. 残留不一致函数清单（7 个）\n")
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
    lines.append("### P0 Loop 区域缺陷（3 个，真算法缺陷）\n")
    lines.append("- **load_get_price** (len_diff -2)：Conditional+BoolOp 嵌套分支残留 2 指令。`if is_utc=='0'` 与 `elif typet==1 or typet==2 or ...` BoolOp 链分支语句部分丢失。违反原则 3（嵌套即抽象节点）+ 原则 4（入口引用语义）。")
    lines.append("- **get_str_data** (len_diff -48)：Loop 嵌套 for/while 循环体语句丢失。`_generate_loop` 在嵌套循环体块遍历漏掉 merge/follow 块。违反原则 2（每块唯一归属）。")
    lines.append("- **get_date_and_count** (len_diff -27)：Loop+Conditional while 循环 if/elif 链语句丢失。while 体内 if/elif 链未完整生成。违反原则 1（自底向上归约）+ 原则 3。\n")
    lines.append("### P1 跳转目标归一化差异（3 个，语义等价）\n")
    lines.append("- **one_prod_to_dataframe** (instr_diff@131)：首个 `i==0` 提取为外层 if，原始跳到下一 elif，跳转目标偏移。归一化已对齐指令索引，残留偏移差异。违反原则 4（入口引用语义）。")
    lines.append("- **build_future_fill_time** (instr_diff@226)：listcomp 内部 code 对象布局 + 后续跳转目标偏移。违反原则 4。")
    lines.append("- **change_his_to_backward** (instr_diff@296)：for 循环内嵌套 if 的 else 体已恢复，残留跳转目标偏移。违反原则 4。\n")
    lines.append("### P2 元数据差异（1 个，非算法缺陷）\n")
    lines.append("- **<module>** (instr_diff)：嵌套 code 对象 co_filename 原始为 `./fly_docker_py311/fly/data/quotation.py`，反编译产物为 `<decompiled>`。违反原则 4（入口引用语义，co_filename 引用语义）。\n")
    lines.append("## 4. 详细 diff\n")
    lines.append(f"见 `diff_detail.txt`（{DIFF_TXT}），含 7 个残留函数 orig vs new 指令逐行对比。\n")
    lines.append("## 5. load_get_price -2 指令详细分析（R11 重点）\n")
    lines.append("`load_get_price` orig_len=226 / new_len=224 / diff=-2，first_diff_idx=164。逐指令 diff 显示：\n")
    lines.append("- **缺失的 2 条指令 = orig idx 198 `LOAD_FAST 'panel'` + idx 199 `STORE_FAST 'panel'`** —— 即 for 循环退出后、`if _typet in (7,8,9,15):` 条件前的冗余自赋值 `panel = panel`，反编译器在 loop-exit → conditional 衔接处丢弃。")
    lines.append("- idx 164 `JUMP_FORWARD`：orig `->[200]` vs new `->[198]`（因前述 2 指令缺失，目标整体前移 2）。")
    lines.append("- idx 168 `POP_JUMP_FORWARD_IF_FALSE`：orig `->[198]` vs new `->[-1]`（new 跳转目标 offset 不在过滤后指令表，BoolOp `_typet in (7,8,9,15)` 条件 then 入口语义未对齐）。")
    lines.append("- idx 197 起后续指令整体偏移 2，orig 在末尾多出 2 条（new idx 223 `RETURN_VALUE` 即结束）。\n")
    lines.append("根因：Loop-exit merge 块与后续 Conditional 区域的衔接未遵循原则 4（入口引用语义）—— 冗余自赋值块作为 loop-exit 的 follow 块未被保留，且 BoolOp 条件入口跳转目标归一化失败。\n")
    lines.append("## 6. 最小复现实例清单\n")
    lines.append("见 `minimal_repros/`，共 10 个 repro（repro_01..repro_10），全部 `py_compile` 通过：\n")
    lines.append("| 文件 | 区域类型 | 违反原则 | 对应函数 |")
    lines.append("|------|----------|----------|----------|")
    lines.append("| repro_01.py | Conditional + BoolOp | 3 + 4 | load_get_price |")
    lines.append("| repro_02.py | Loop + Conditional | 2 + 4 | load_get_price (-2 指令: panel=panel) |")
    lines.append("| repro_03.py | BoolOp + Conditional | 4 | load_get_price (in tuple 跳转 -1) |")
    lines.append("| repro_04.py | Loop | 2 | get_str_data (-48) |")
    lines.append("| repro_05.py | Loop + Conditional | 1 + 3 | get_date_and_count (-27) |")
    lines.append("| repro_06.py | Conditional | 4 | one_prod_to_dataframe |")
    lines.append("| repro_07.py | Sequence + Conditional | 4 | build_future_fill_time |")
    lines.append("| repro_08.py | Loop + Conditional | 4 | change_his_to_backward |")
    lines.append("| repro_09.py | Module | 4 | <module> (co_filename) |")
    lines.append("| repro_10.py | Conditional + BoolOp | 3 + 4 | load_get_price (多层嵌套综合) |")
    lines.append("")
    lines.append("重点 repro_02 直接复现 -2 指令根因（循环退出后 `panel = panel` 自赋值被丢弃）。")
    with open(REPORT_MD, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"[diff_detail] wrote {DIFF_TXT}")
    print(f"[report] wrote {REPORT_MD}")
    for name in FOCUS:
        r = results.get(name, {})
        if r.get('status') == 'len_diff':
            print(f"  {name}: len_diff {r['orig_len']}->{r['new_len']} ({r['diff']:+d})")
        elif r.get('status') == 'instr_diff':
            print(f"  {name}: instr_diff@{r['first_diff_idx']} orig={r['orig_at']} new={r['new_at']}")
        else:
            print(f"  {name}: {r.get('status', '?')}")


if __name__ == '__main__':
    main()
