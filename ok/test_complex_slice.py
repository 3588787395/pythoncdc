"""测试复杂切片表达式"""

def func(panel, source_start, source_end):
    # 复杂的切片表达式：使用元组作为索引
    result = panel.ix[:, source_start:source_end]
    return result
