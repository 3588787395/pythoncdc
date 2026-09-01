"""分析多 seed 产物快照的差异，并归因是否为「集合字面量元素顺序」。"""
import os
import re
import sys
import difflib

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(HERE, 'variants')
SEEDS = ['0', '1', '2']
SHOW = int(sys.argv[1]) if len(sys.argv) > 1 else 3


def load(seed, name):
    p = os.path.join(V, 'seed_%s' % seed, name)
    return open(p, encoding='utf-8', errors='replace').read().splitlines()


def norm_literals(s):
    """把行内 (...) / {...} 的元素排序，消除顺序差异。"""
    def rep(m):
        body = m.group(1)
        parts = [p.strip() for p in body.split(',') if p.strip()]
        if not parts:
            return m.group(0)
        return m.group(0)[0] + ', '.join(sorted(parts)) + m.group(0)[-1]
    return re.sub(r'[\(\{]([^\(\)\{\}]*)[\)\}]', rep, s)


def main():
    names = sorted(os.listdir(os.path.join(V, 'seed_0')))
    print('%-46s %7s %7s  %s' % ('文件', 'diff行', '总行数', '仅顺序差异'))
    print('-' * 82)
    tot_files = tot_diff = tot_order = 0
    shown = 0
    for n in names:
        base = {s: load(s, n) for s in SEEDS}
        all_diff = []
        only_order = True
        for s in SEEDS[1:]:
            a, b = base[SEEDS[0]], base[s]
            sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
            ops = [(a[i1:i2], b[j1:j2])
                   for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != 'equal']
            for x, y in ops:
                if len(x) != len(y) or not x:
                    only_order = False
                    all_diff.append(('结构性', x[:1], y[:1]))
                    continue
                for la, lb in zip(x, y):
                    if norm_literals(la) != norm_literals(lb):
                        only_order = False
                        all_diff.append(('非顺序', la.strip(), lb.strip()))
                    else:
                        all_diff.append(('顺序', la.strip(), lb.strip()))
        # 用 (0 vs 1) 的行数代表单对 diff 规模
        a, b = base['0'], base['1']
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        ndiff = sum(max(i2 - i1, j2 - j1)
                    for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != 'equal')
        tot_files += 1
        tot_diff += ndiff
        if only_order:
            tot_order += ndiff
        print('%-46s %7d %7d  %s' % (n.replace('__', '/'), ndiff, len(a),
                                     'YES' if only_order else 'NO'))
        if shown < SHOW:
            for kind, la, lb in all_diff[:2]:
                print('      [%s]' % kind)
                print('        seed0: %s' % la[:110])
                print('        seed1: %s' % lb[:110])
            shown += 1
    print('-' * 82)
    print('不可复现文件 %d 个；单对(seed0 vs seed1)差异行合计 %d，其中仅字面量元素顺序 %d 行 (%.1f%%)'
          % (tot_files, tot_diff, tot_order, 100 * tot_order / tot_diff if tot_diff else 0))


if __name__ == '__main__':
    main()
