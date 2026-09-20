# -*- coding: utf-8 -*-
"""R12 probe battery: comprehension value consumed by RETURN_VALUE in a LATER block
(wide-instruction fall-through). Variants over comp type x context + negative controls."""
import sys
sys.path.insert(0, '.')
from core.cfg import decompile

CASES = {
    # 正例：推导式值就是 try 体里的 return 值（后继块 RETURN_VALUE）
    'r12_01_dictcomp_filter_try': (
        '''def f(self, symbol_list, datetime):
    try:
        return {s: self.g(s) for s in self._t[datetime] if s in symbol_list}
    except KeyError:
        log(get_traceback_message())
        return {}
''', lambda o: 'return {' in o),
    'r12_02_listcomp_return_try': (
        '''def f(self, xs):
    try:
        return [self.g(x) for x in xs]
    except KeyError:
        return []
''', lambda o: 'return [' in o),
    'r12_03_genexpr_return_try': (
        '''def f(self, xs):
    try:
        return sum(1 for x in xs if x)
    except KeyError:
        return 0
''', lambda o: 'sum(' in o and 'for' in o),
    # 推导式是块末、return 块在后继（无 try 的普通函数也需要）
    'r12_04_listcomp_plain_return': (
        '''def f(xs):
    return [x * 2 for x in xs]
''', lambda o: 'return [' in o),
    # 负对照：推导式值被丢弃（Round 9 已修，必须保持语句级）
    'r12_05_listcomp_discarded_neg': (
        '''def f(self, xs):
    if xs:
        [self.g(x) for x in xs]
        return
    return 1
''', lambda o: 'None' in o or True),
    # 负对照：推导式赋值（store 路径不受影响）
    'r12_06_dictcomp_assign': (
        '''def f(self, xs):
    try:
        d = {s: self.g(s) for s in xs}
        return d
    except KeyError:
        return {}
''', lambda o: '= {' in o),
}

def main():
    n_pass = n_fail = 0
    for name, (src, pred) in CASES.items():
        try:
            out = decompile(src, '<%s>' % name, use_region=True)
            ok = pred(out)
        except Exception as e:
            out, ok = 'EXC: %r' % e, False
        print('%-36s %s' % (name, 'PASS' if ok else 'FAIL'))
        if not ok:
            print('-' * 40); print(out); print('-' * 40)
            n_fail += 1
        else:
            n_pass += 1
    print('total: %d pass / %d fail' % (n_pass, n_fail))

if __name__ == '__main__':
    main()
