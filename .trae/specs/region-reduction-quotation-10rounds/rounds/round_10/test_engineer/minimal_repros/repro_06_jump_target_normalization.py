"""R10 repro_06: one_prod_to_dataframe 跳转目标归一化差异（instr_diff@131，R8 已修复 len）。
缺陷: 反编译器将首个 `i==0` 提取为外层 if，原始跳到下一 elif，导致跳转目标偏移(语义等价)。
区域类型: Conditional  违反原则: 4(入口引用语义)
"""
def f(prod):
    index = []
    i = 0
    for v in prod:
        if i == 0 and len(v) == 8:
            index.append(v)
        elif i == 0 and len(v) == 10:
            index.append(v)
        elif i == 0 and len(v) == 9:
            index.append(v)
        i = i + 1
    return index
