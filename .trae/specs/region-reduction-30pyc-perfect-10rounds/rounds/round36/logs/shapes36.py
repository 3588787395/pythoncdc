# -*- coding: utf-8 -*-
"""Round 36 G0: the shape where a whole `for` statement disappears from the product.

一手靶子（landed 703be216 实测）：`IQEngine/plugins/plugin_fly_data/fly_api/base.pyc` 的两个孪生方法
    def has_close_position_type(self, transaction_code):
        for i, c in enumerate(transaction_code):
            if c.isdigit():
                transaction_code = transaction_code[:i]
                break
        return transaction_code in self._store          # orig 27 -> decomp 6
    def get_close_position_type(...):  ... same loop ... return self._store.get(x, STYLE)  # 30 -> 9
即：循环体的唯一语句是「if + 带副作用的赋值 + break」，且 break 的目标就是 FOR_ITER 的耗尽落点
（循环没有 else 子句）。整条 for 语句连同它的赋值一起消失。

These shapes are the boundary probe for that claim: which neighbours of the shape still decompile
today, and which collapse the same way. Nothing here is written into the repo by this file; the
runner writes the .py/.pyc pair into the test_repros dir passed on the command line.

usage: python -X utf8 shapes36.py            # only prints the sources
"""

HEAD = 'STORE = {}\n\n'

SHAPES = {
    # 见证：与靶子逐条同形（orig 27 条，循环整体消失 ⇒ 必须 FAIL）
    'r36_01_witness_for_body_is_if_with_sideeffect_break': (HEAD + '''
def f(tc):
    for i, c in enumerate(tc):
        if c.isdigit():
            tc = tc[:i]
            break
    return tc in STORE
'''),

    # 靶子的孪生半：出口语句是 .get(k, default) 而不是 `k in store`
    'r36_02_witness_exit_is_call_with_default': (HEAD + '''
def f(tc):
    for i, c in enumerate(tc):
        if c.isdigit():
            tc = tc[:i]
            break
    return STORE.get(tc, 3)
'''),

    # 控制：循环之后还有一条语句才到出口（汇合块不再同时是「函数尾」）
    'r36_03_control_statement_between_loop_and_exit': (HEAD + '''
def f(tc):
    for i, c in enumerate(tc):
        if c.isdigit():
            tc = tc[:i]
            break
    tc = tc.strip()
    return tc in STORE
'''),

    # 控制：break 没有副作用（体内没有赋值），最小程序
    'r36_04_control_break_without_sideeffect': (HEAD + '''
def f(tc):
    for i, c in enumerate(tc):
        if c.isdigit():
            break
    return tc in STORE
'''),

    # 控制：有 else 子句 ⇒ break 目标与耗尽落点不同（R20-A 已收口的形状）
    'r36_05_control_for_else_break_target_differs': (HEAD + '''
def f(tc):
    for i, c in enumerate(tc):
        if c.isdigit():
            tc = tc[:i]
            break
    else:
        tc = 'x'
    return tc in STORE
'''),

    # 控制：循环体里 if 之前还有一条语句（体不是「只有 if」）
    'r36_06_control_body_has_leading_statement': (HEAD + '''
def f(tc):
    for i, c in enumerate(tc):
        n = len(tc)
        if c.isdigit():
            tc = tc[:i]
            break
    return tc in STORE
'''),

    # 控制：if 臂里赋值之后不 break（体尾自然落回边）
    'r36_07_control_no_break_at_all': (HEAD + '''
def f(tc):
    for i, c in enumerate(tc):
        if c.isdigit():
            tc = tc[:i]
    return tc in STORE
'''),
}

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    for k in sorted(SHAPES):
        print('=' * 20, k)
        print(SHAPES[k])
