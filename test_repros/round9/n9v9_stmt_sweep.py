def raise_deep(a, b):
    # Raise 形态：深层宿主（try 体 + 循环内）
    for i in range(3):
        try:
            if a > b:
                raise ValueError(i)
        except ValueError:
            a -= 1
    return a


def raise_from(a, b):
    # Raise from 形态 × 嵌套 with 宿主
    with open('x') as f:
        try:
            raise KeyError(a) from TypeError(b)
        except KeyError:
            return a
    return b


def assert_deep(a, b):
    # Assert 形态：嵌套循环 + 条件复合
    for i in range(3):
        while a < b:
            assert 0 < a < b, a
            a += 1
    return a


def pass_arms(a, b):
    # Pass 形态：if/else/except/finally 四臂 pass
    try:
        if a > b:
            pass
        else:
            a = b
    except OSError:
        pass
    finally:
        pass
    return a


def expr_stmt_deep(a, b, sink):
    # Expr 形态：纯表达式语句 × 深层宿主（调用语句 + f-string 语句）
    for i in range(2):
        with open('y') as f:
            sink(f.read())
            f"got {a} and {b!r}"
    return None
