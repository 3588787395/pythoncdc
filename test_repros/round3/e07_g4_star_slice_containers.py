# e07: 星号解包 Call/赋值、切片嵌套下标、容器嵌套 >=3 层、深宿主
def f_star_call(a, rest, kw):
    def sink(x, *rs, flag=False, **ks):
        return x + sum(rs) + (1 if flag else 0) + len(ks)
    for i in range(3):
        if i:
            while i:
                return sink(a, *rest, flag=True, **kw)
    return 0


def f_star_call_mixed(a, rest, kw):
    def sink(x, y, *rs, z=1, **ks):
        return x + y + sum(rs) + z + len(ks)
    for i in range(3):
        if i:
            while i:
                return sink(a, 2, *rest, z=3, **kw)
    return 0


def f_star_assign(xs):
    for i in range(3):
        if i:
            while i:
                a, *b = xs
                return a, b
    return 0


def f_star_assign_head(xs):
    for i in range(3):
        if i:
            while i:
                *a, b = xs
                return a, b
    return 0


def f_star_assign_mid(xs):
    for i in range(3):
        if i:
            while i:
                a, *b, c = xs
                return a, b, c
    return 0


def f_slice_nested_sub(m, i, j):
    for k in range(3):
        if k:
            while k:
                return m[i:j, k] + m[1:2, 3]
    return 0


def f_slice_steps(xs, w):
    for i in range(3):
        if i:
            while i:
                return xs[::-1] + xs[:: w] + xs[1 : -1 : 2]
    return 0


def f_slice_expr_bounds(xs, a, b):
    for i in range(3):
        if i:
            while i:
                return xs[a + 1 : b * 2] + xs[a if b else 0 : 3]
    return 0


def f_container_nest3(d):
    for i in range(3):
        if i:
            while i:
                return {'a': [1, (2, {3, 4})], 'b': {'c': [5, 6]}}[d]
    return 0


def f_container_mixed(a, b):
    for i in range(3):
        if i:
            while i:
                return ([a, (b, [a])], {a: {b: [1, 2]}}, {a, (b,)})
    return 0


def f_subscript_deep(m, i, j):
    for k in range(3):
        if k:
            while k:
                return m[i][j][k] + m[i][j : k]
    return 0


def f_tuple_in_call(a, b, c):
    def sink(t):
        return sum(t)
    for i in range(3):
        if i:
            while i:
                return sink((a, b, c)) + sink([a, b])
    return 0
