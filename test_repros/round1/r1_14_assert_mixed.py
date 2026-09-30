# r1_14 assert 语句上下文混合链（assert a and b or c）
# 焦点：ASSERT 形态的 BoolOp 条件消费


def f(a, b, c):
    assert a and b or c
    return 1
