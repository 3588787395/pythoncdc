# 复杂生成器测试
def complex_generator(n):
    """生成器，包含多种yield用法"""
    for i in range(n):
        if i % 2 == 0:
            yield i * 2
        else:
            yield i * 3

def generator_with_send():
    """支持send的生成器"""
    total = 0
    while True:
        value = yield total
        if value is None:
            break
        total += value
    return total

# 生成器表达式
gen_expr = (x * x for x in range(10) if x % 2 == 0)
