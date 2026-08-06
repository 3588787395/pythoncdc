"""R35 最小复现实例 3: EXTENDED_ARG 差异"""
# 原始: EXTENDED_ARG 参数值依赖字节码布局
# 反编译: 不同布局导致不同 EXTENDED_ARG 值
# 预期: 过滤 EXTENDED_ARG 后字节码一致

def func_with_many_vars(a, b, c, d, e, f, g, h, i, j):
    if a > 0:
        if b > 0:
            if c > 0:
                return a + b + c + d + e + f + g + h + i + j
    return 0
