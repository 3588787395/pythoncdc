"""R23 测试工程师：按函数输出不一致指令 diff，生成 diff_detail.txt。

R23 是 V3 10 轮迭代的第 3 轮，重点攻克 get_str_data 残留 instr_diff@179 根因
（continue 作为 if 兄弟语句发射问题）。FOCUS 为 V3 残留的 3 个不一致函数（<module>
已在 R17 修复，不再列入）：
- get_str_data: instr_diff@179 (317=317) — POP_JUMP_FORWARD_IF_FALSE 跳转目标
  orig=182 (→JUMP_BACKWARD 回边 = continue 兄弟) vs new=183 (→post-loop = break 内嵌)
- change_his_to_backward: instr_diff@296 — code_generator if/else 分支布局未对齐
- get_date_and_count: len_diff -27 (714→687) — Loop 反向链吸收外层条件块 + loop_else
"""
import sys, json, types, dis, os

sys.path.insert(0, '/workspace')
# 从同目录的 exact_match_stats.py 导入归一化逻辑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exact_match_stats import get_instr_list, walk_code, load_orig, PYC, DECOMPILED, OUT_DIR, JUMP_OPS, SKIP_OPS

DIFF_TXT = OUT_DIR + '/diff_detail.txt'

# R23 FOCUS：3 个残留函数（<module> 已在 R17 修复）
FOCUS = ['get_str_data', 'change_his_to_backward', 'get_date_and_count']


def fmt(ins):
    off, op, av = ins
    if isinstance(av, tuple) and av[0] == 'J':
        return f"{off:>4} {op:<28} ->[{av[1]}]"
    if isinstance(av, types.CodeType):
        return f"{off:>4} {op:<28} <code {av.co_name}> fn={av.co_filename!r}"
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
        fh.write("# R23 diff_detail — 3 个残留不一致函数逐指令 diff\n")
        fh.write(f"# summary: total={summary['total']} matched={summary['matched']} "
                 f"mismatched={summary['mismatched']} success_rate={summary['success_rate_pct']}% "
                 f"compile_ok={summary['compile_ok']}\n")
        fh.write(f"# orig PYC={PYC}\n")
        fh.write(f"# new  SRC={DECOMPILED}\n")
        for name in FOCUS:
            if name not in orig_cos or name not in new_cos:
                fh.write(f"\n=== {name}: MISSING ===\n")
                continue
            oa = get_instr_list(orig_cos[name])
            na = get_instr_list(new_cos[name])
            dump_pair(name, oa, na, fh)

    print(f"[diff_detail] wrote {DIFF_TXT}")
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
