"""repro_07: TernaryRegion as dict value in loop body (get_str_data 'price' 字段)
区域类型: Loop + TernaryRegion(merge_context='store')
违反原则: 3 (嵌套即抽象节点) + 4 (入口引用语义)
对应函数: get_str_data (data[i] = {..., 'price': ternary, ...})
缺陷镜像: `for i in idx: data[i] = {'open': 0, 'price': a if c else b, 'money': 0}`
  TernaryRegion(a if c else b) 的 merge_block 含 BUILD_CONST_KEY_MAP + STORE_SUBSCR。
  merge_context='store'，ternary 结果作为 dict 字面量元素。
  若 IfRegion(continue) else 不分发 TernaryRegion，dict 字面量赋值整段丢失。
  违反原则 3（TernaryRegion 应作为抽象节点）+ 原则 4（else 应引用子区域 entry）。
"""


def f(idx, a, b, c):
    data = {}
    for i in idx:
        if not i:
            continue
        data[i] = {'open': 0, 'close': 0, 'high': 0, 'low': 0, 'volume': 0,
                   'price': a if c else b, 'money': 0}
    return data
