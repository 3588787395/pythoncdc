"""对比两份 full_scan.py 明细结果，列出倒退与改善。

用法: D:/Python/python.exe compare_results.py <新结果.json> <基线.json>
"""
import json
import sys


def load(path):
    d = json.load(open(path, encoding='utf-8'))
    rows = d['results']
    out = {}
    for r in rows:
        out[r['path']] = {
            'status': r.get('status'),
            'rate': r.get('rate', 0.0),
            'ok': r.get('matched_functions', 0),
            'total': r.get('total_functions', 0),
            'error': r.get('error'),
        }
    return d.get('summary', {}), out


def main():
    _, new = load(sys.argv[1])
    _, base = load(sys.argv[2])

    rank = {'ok': 3, 'partial': 2, 'failed': 1, None: 0}
    regs, imps = [], []
    for p, n in new.items():
        b = base.get(p)
        if b is None:
            continue
        ns, bs = n['status'], b['status']
        if rank.get(ns, 0) < rank.get(bs, 0):
            regs.append((p, bs, ns, b, n))
        elif rank.get(ns, 0) > rank.get(bs, 0):
            imps.append((p, bs, ns, b, n))
        elif ns in ('partial', 'ok'):
            if n['ok'] < b['ok']:
                regs.append((p, bs, ns, b, n))
            elif n['ok'] > b['ok']:
                imps.append((p, bs, ns, b, n))

    print('=== 倒退 (%d) ===' % len(regs))
    for p, bs, ns, b, n in sorted(regs, key=lambda x: (x[1], x[0])):
        print('  %-8s -> %-8s  funcs %s/%s -> %s/%s  %s'
              % (bs, ns, b['ok'], b['total'], n['ok'], n['total'],
                 p.replace('F:/Downloads/pythoncdc-main/', '')))
        if n.get('error'):
            print('      error: %s' % str(n['error'])[:160])
    print()
    print('=== 改善 (%d) ===' % len(imps))
    for p, bs, ns, b, n in sorted(imps, key=lambda x: x[0]):
        print('  %-8s -> %-8s  funcs %s/%s -> %s/%s  %s'
              % (bs, ns, b['ok'], b['total'], n['ok'], n['total'],
                 p.replace('F:/Downloads/pythoncdc-main/', '')))

    for label, m in (('BASE', base), ('NEW ', new)):
        ok = sum(1 for v in m.values() if v['status'] == 'ok')
        pt = sum(1 for v in m.values() if v['status'] == 'partial')
        fl = sum(1 for v in m.values() if v['status'] == 'failed')
        fo = sum(v['ok'] for v in m.values())
        ft = sum(v['total'] for v in m.values())
        print()
        print('%s: ok=%d partial=%d failed=%d funcs=%d/%d'
              % (label, ok, pt, fl, fo, ft))


if __name__ == '__main__':
    main()
