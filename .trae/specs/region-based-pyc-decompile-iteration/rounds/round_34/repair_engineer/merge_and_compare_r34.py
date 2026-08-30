"""Round 34: 合并 3 分片扫描结果 + 与 round_33 基线对比。

用法: D:/Python/python.exe merge_and_compare_r34.py
产出:
  scan_after_fix2_r34.json   合并后的完整扫描结果
  控制台: 总体统计、回归清单、改进清单、不变清单
"""
import json
import os

ROUND34 = r'F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_34\repair_engineer'
ROUND33 = r'F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_33\repair_engineer'

PARTS = ['scan_fix2_part_a.json', 'scan_fix2_part_b.json', 'scan_fix2_part_c.json']
BASELINE = os.path.join(ROUND33, 'scan_after_fix2.json')
OUT = os.path.join(ROUND34, 'scan_after_fix2_r34.json')


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def norm(p):
    return os.path.normcase(os.path.normpath(p.replace('\\', '/')))


def main():
    merged = {'summary': {'ok': 0, 'partial': 0, 'failed': 0,
                          'matched_functions': 0, 'total_functions': 0,
                          'elapsed_sec': 0.0},
              'results': []}
    for part in PARTS:
        p = os.path.join(ROUND34, part)
        if not os.path.exists(p):
            print('MISSING part:', p)
            continue
        data = load(p)
        merged['results'].extend(data['results'])
        s = data['summary']
        merged['summary']['ok'] += s['ok']
        merged['summary']['partial'] += s['partial']
        merged['summary']['failed'] += s['failed']
        merged['summary']['matched_functions'] += s['matched_functions']
        merged['summary']['total_functions'] += s['total_functions']
        merged['summary']['elapsed_sec'] += s['elapsed_sec']
        print('part %s: ok=%d partial=%d failed=%d funcs=%d/%d'
              % (part, s['ok'], s['partial'], s['failed'],
                 s['matched_functions'], s['total_functions']))

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=1)
    print('merged written ->', OUT)
    print('SUMMARY ok=%d partial=%d failed=%d funcs=%d/%d'
          % (merged['summary']['ok'], merged['summary']['partial'],
             merged['summary']['failed'],
             merged['summary']['matched_functions'],
             merged['summary']['total_functions']))

    # ---- 与基线对比 ----
    base = load(BASELINE)
    base_map = {norm(r['path']): r for r in base['results']}
    cur_map = {norm(r['path']): r for r in merged['results']}

    regress, improve, same, only_new, only_gone = [], [], [], [], []
    for name, cur in cur_map.items():
        b = base_map.get(name)
        if b is None:
            only_new.append(name)
            continue
        b_rate = b.get('rate', 0.0)
        c_rate = cur.get('rate', 0.0)
        if c_rate < b_rate - 1e-9:
            regress.append((name, b['status'], cur['status'], b_rate, c_rate))
        elif c_rate > b_rate + 1e-9:
            improve.append((name, b['status'], cur['status'], b_rate, c_rate))
        else:
            same.append(name)
    for name in base_map:
        if name not in cur_map:
            only_gone.append(name)

    print('\n==== 对比 round_33 基线 ====')
    print('文件总数: base=%d cur=%d' % (len(base_map), len(cur_map)))
    print('回归(rate 下降): %d' % len(regress))
    for name, bs, cs, br, cr in sorted(regress):
        print('  REGRESS %-40s %s(%.4f) -> %s(%.4f)' % (name, bs, br, cs, cr))
    print('改进(rate 上升): %d' % len(improve))
    for name, bs, cs, br, cr in sorted(improve, key=lambda x: -x[4]):
        print('  IMPROVE %-40s %s(%.4f) -> %s(%.4f)' % (name, bs, br, cs, cr))
    print('未变: %d' % len(same))
    print('新增(基线无): %d' % len(only_new))
    print('消失(当前无): %d' % len(only_gone))

    # ---- 状态迁移矩阵 ----
    print('\n==== 状态迁移 (base -> cur) ====')
    matrix = {}
    for name, cur in cur_map.items():
        b = base_map.get(name)
        bs = b['status'] if b else 'NEW'
        cs = cur['status']
        matrix.setdefault((bs, cs), []).append(name)
    for (bs, cs), names in sorted(matrix.items()):
        if bs == cs:
            continue
        print('  %s -> %s : %d  %s' % (bs, cs, len(names),
                                       ', '.join(names[:5])))

    # 汇总 baseline 状态 -> 当前汇总
    from collections import Counter
    print('\n==== 当前状态分布 ====')
    print(Counter(r['status'] for r in merged['results']))


if __name__ == '__main__':
    main()
