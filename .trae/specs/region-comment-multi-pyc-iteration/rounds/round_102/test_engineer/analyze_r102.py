#!/usr/bin/env python3
"""R102 progress.json 分析：升级候选 / 疑似回归 / ok 回归 / 全局推算 / 提名."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROGRESS = HERE / 'progress.json'
INDEX = HERE.parents[5] / 'pyc_index.json'


def main():
    prog = json.loads(PROGRESS.read_text(encoding='utf-8'))
    results = prog['results']
    index = {e['path']: e for e in json.loads(INDEX.read_text(encoding='utf-8'))}

    print(f'total recorded: {len(results)}')
    by_subset = {}
    for r in results.values():
        by_subset.setdefault(r['index_status'], []).append(r)
    for k, v in by_subset.items():
        print(f'  subset from index_status={k}: {len(v)}')

    # ── 1. partial 集合 ──
    partials = list(by_subset.get('partial', []))
    upgrades, suspects, same_or_better = [], [], []
    for r in sorted(partials, key=lambda x: x['pyc']):
        e = index[r['pyc']]
        idx_rate = e.get('bytecode_match_rate', 0.0)
        idx_fc = e.get('function_count', 0)
        new_total = r.get('total_functions', 0)
        new_matched = r.get('matched_functions', 0)
        # 索引隐含 matched 数按新 total 折算（消除 <module> 计数差异）
        implied_matched = idx_rate * new_total
        dropped = round(implied_matched) - new_matched  # >0 表示下降
        if r.get('match_rate') == 1.0:
            upgrades.append((r, e))
        elif dropped >= 1:
            suspects.append((r, e, dropped))
        else:
            same_or_better.append((r, e, dropped))

    print(f'\n=== A. partial rate=1.0 可升级 ({len(upgrades)}) ===')
    for r, _ in upgrades:
        print(f"  {r['pyc']}\n    measured: total={r['total_functions']} "
              f"matched={r['matched_functions']} rate={r['match_rate']}")

    print(f'\n=== B. partial 疑似回归（相对索引下降>=1函数）({len(suspects)}) ===')
    for r, e, d in suspects:
        print(f"  {r['pyc']}\n    index: status={e.get('decompile_status')} "
              f"rate={e.get('bytecode_match_rate')} fc={e.get('function_count')} | "
              f"measured: total={r['total_functions']} matched={r['matched_functions']} "
              f"rate={r.get('match_rate'):.4f} | dropped={d}")

    n_worse = sum(1 for _, _, d in same_or_better if d <= -1)
    print(f'\n  (partial 其余 {len(same_or_better)} 个持平或改善, 其中改善>=1函数的 '
          f'{n_worse} 个)')

    # ── 2. ok-sample ──
    oks = list(by_subset.get('ok', []))
    bad_ok = [r for r in oks if r.get('status') != 'ok' or r.get('match_rate') != 1.0]
    print(f'\n=== C. ok-sample 不一致 ({len(bad_ok)}/{len(oks)}) ===')
    for r in sorted(bad_ok, key=lambda x: x['pyc']):
        print(f"  {r['pyc']}\n    measured: status={r.get('status')} "
              f"total={r['total_functions']} matched={r['matched_functions']} "
              f"rate={r.get('match_rate')} mismatches={len(r.get('mismatches', []))}")
        for m in r.get('mismatches', []):
            print(f"      - {m['name']}: orig={m['orig_count']} decomp={m['decomp_count']} "
                  f"jump_diffs={m['jump_diffs']} true_diffs={m['true_diffs']}")
            fd = m.get('first_diff')
            if fd:
                print(f"        first_diff: {json.dumps(fd, ensure_ascii=False)[:220]}")
    anomalous = [r for r in oks if r.get('status') in ('timeout', 'crashed', 'missing')]
    print(f'  (异常状态: {len(anomalous)})')

    # ── 3. 全局推算 ──
    entries = list(index.values())
    base_ok = sum(1 for e in entries if e.get('decompile_status') == 'ok')
    tot_f = sum(e.get('function_count', 0) for e in entries if e.get('last_tested_round', 0) > 0)
    mat_f = sum(int(round(e.get('function_count', 0) * e.get('bytecode_match_rate', 0.0)))
                for e in entries if e.get('last_tested_round', 0) > 0)
    print('\n=== D. 全局统计推算 ===')
    print(f'  索引现状: ok={base_ok} partial=112 failed=0 funcs={tot_f} '
          f'matched={mat_f} rate={mat_f / tot_f:.2%}')
    # 升级：partial->ok，其函数贡献改为实测 total（全匹配）
    proj_tot, proj_mat = tot_f, mat_f
    for r, _ in upgrades:
        e = index[r['pyc']]
        old_contrib = int(round(e.get('function_count', 0) * e.get('bytecode_match_rate', 0.0)))
        proj_mat += int(round(r['total_functions'])) - old_contrib
    n_ok2 = base_ok + len(upgrades)
    print(f'  若 {len(upgrades)} 个 partial(rate=1.0) 升级 ok:')
    print(f'    ok={n_ok2} partial={112 - len(upgrades)} failed=0')
    print(f'    matched={proj_mat}/{proj_tot} rate={proj_mat / proj_tot:.2%}')

    # ok-sample 回归对全局的影响（保守外推仅计实测）
    for r in bad_ok:
        e = index[r['pyc']]
        old_contrib = int(round(e.get('function_count', 0) * 1.0))
        new_contrib = r.get('matched_functions', 0)
        proj_mat -= (old_contrib - new_contrib)
    print(f'  再计入 ok-sample 实测回归 ({len(bad_ok)} 个): matched={proj_mat}/{proj_tot} '
          f'rate={proj_mat / proj_tot:.2%}')

    # ── 4. 修复提名：剩余不匹配函数最少 且 非 <module>-only ──
    remaining = [r for r in partials if r.get('match_rate') != 1.0 and r.get('mismatches')]
    non_module_only = []
    for r in remaining:
        mis = r['mismatches']
        nm = [m for m in mis if m['name'] != '<module>']
        if nm:
            non_module_only.append((r, nm))
    non_module_only.sort(key=lambda t: (len(t[1]), -(t[0].get('match_rate') or 0)))
    print(f'\n=== E. 提名候选（非 <module>-only，剩余不匹配函数升序）前 10 ===')
    for r, nm in non_module_only[:10]:
        rel = r['pyc'].replace('F:/Downloads/pythoncdc-main/', '')
        print(f"  {rel}  total={r['total_functions']} matched={r['matched_functions']} "
              f"rate={r['match_rate']:.4f} 剩余不匹配函数数={len(nm)}")
        for m in nm:
            print(f"      - {m['name']}: orig={m['orig_count']} decomp={m['decomp_count']} "
                  f"jump_diffs={m['jump_diffs']} true_diffs={m['true_diffs']}")
            fd = m.get('first_diff')
            if fd:
                print(f"        first_diff: {json.dumps(fd, ensure_ascii=False)[:260]}")

    # 附：<module>-only 且剩余最少的（备选参考）
    mod_only = [(r, r['mismatches']) for r in remaining
                if all(m['name'] == '<module>' for m in r['mismatches'])]
    mod_only.sort(key=lambda t: (len(t[1][0].get('true_diffs', 0)) if False else
                                 sum(m['true_diffs'] for m in t[1])))
    print(f'\n=== F. 参考: <module>-only 剩余 partial 共 {len(mod_only)} 个; true_diffs 最小前 3 ===')
    for r, mis in mod_only[:3]:
        rel = r['pyc'].replace('F:/Downloads/pythoncdc-main/', '')
        for m in mis:
            print(f"  {rel} rate={r['match_rate']:.4f} <module>: orig={m['orig_count']} "
                  f"decomp={m['decomp_count']} true_diffs={m['true_diffs']}")


if __name__ == '__main__':
    sys.exit(main())
