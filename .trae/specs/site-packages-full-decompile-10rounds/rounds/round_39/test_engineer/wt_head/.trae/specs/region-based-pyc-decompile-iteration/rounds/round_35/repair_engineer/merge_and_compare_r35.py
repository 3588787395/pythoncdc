"""Round 35: 与 round_34 基线逐文件对比（全路径 key，串行扫描结果）。

用法: D:/Python/python.exe merge_and_compare_r35.py
产出: 控制台汇总（总体统计 / 回归 / 改进 / 不变）
"""
import json
import os

ROUND35 = r'F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_35\repair_engineer'
ROUND34 = r'F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_34\repair_engineer'

SCAN = os.path.join(ROUND35, 'scan_after_fix_r35.json')
BASELINE = os.path.join(ROUND34, 'scan_after_fix2_r34.json')


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def norm(p):
    return os.path.normcase(os.path.normpath(p.replace('\\', '/')))


def get_files(data):
    """返回 {normpath: {status, matched, total, rate}}"""
    out = {}
    files = data.get('files') or data.get('results') or []
    if isinstance(data, list):
        files = data
    for rec in files:
        p = rec.get('path') or rec.get('file') or rec.get('pyc')
        if not p:
            continue
        out[norm(p)] = {
            'status': rec.get('status'),
            'matched': rec.get('matched_functions') or rec.get('matched') or 0,
            'total': rec.get('total_functions') or rec.get('total') or 0,
            'rate': rec.get('rate') or rec.get('match_rate') or 0.0,
        }
    return out


def main():
    scan = load(SCAN)
    base = load(BASELINE)
    cur = get_files(scan)
    prev = get_files(base)

    print('当前扫描文件数: %d, 基线文件数: %d' % (len(cur), len(prev)))

    # 总体统计（当前）
    s_ok = s_part = s_fail = 0
    m_f = t_f = 0
    for p, r in cur.items():
        st = r['status']
        if st == 'ok':
            s_ok += 1
        elif st == 'partial':
            s_part += 1
        elif st == 'failed':
            s_fail += 1
        m_f += r['matched']
        t_f += r['total']
    print('\n== 总体(当前): ok=%d / partial=%d / failed=%d / 函数 %d/%d ==' % (
        s_ok, s_part, s_fail, m_f, t_f))

    regress = []
    improve = []
    unchanged = 0
    for p, r in cur.items():
        if p not in prev:
            continue
        b = prev[p]
        if b['status'] != r['status']:
            if r['status'] == 'failed':
                regress.append((p, b['status'], r['status'], b['matched'], r['matched']))
            elif b['status'] == 'failed':
                improve.append((p, b['status'], r['status'], b['matched'], r['matched']))
            elif b['status'] == 'partial' and r['status'] == 'ok':
                improve.append((p, b['status'], r['status'], b['matched'], r['matched']))
            elif b['status'] == 'ok' and r['status'] == 'partial':
                regress.append((p, b['status'], r['status'], b['matched'], r['matched']))
            else:
                # ok->failed / failed->ok 等
                if b['matched'] > r['matched']:
                    regress.append((p, b['status'], r['status'], b['matched'], r['matched']))
                else:
                    improve.append((p, b['status'], r['status'], b['matched'], r['matched']))
        elif r['status'] in ('partial', 'ok') and r['matched'] != b['matched']:
            if r['matched'] > b['matched']:
                improve.append((p, b['status'], r['status'], b['matched'], r['matched']))
            else:
                regress.append((p, b['status'], r['status'], b['matched'], r['matched']))
        else:
            unchanged += 1

    print('\n== 回归: %d ==' % len(regress))
    for p, bs, cs, bm, cm in sorted(regress):
        print('  %-70s %s(%d) -> %s(%d)' % (p, bs, bm, cs, cm))
    print('\n== 改进: %d ==' % len(improve))
    for p, bs, cs, bm, cm in sorted(improve):
        print('  %-70s %s(%d) -> %s(%d)' % (p, bs, bm, cs, cm))
    print('\n== 不变: %d ==' % unchanged)


if __name__ == '__main__':
    main()
