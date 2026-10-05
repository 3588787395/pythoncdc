# e06: 操作符叶子全遍历——BinOp 13 + Compare 16 + UnaryOp 4（Add..NotIn + USub/UAdd/Invert/Not）
def f_binop_arith(a, b):
    for i in range(3):
        if i:
            while i:
                return (a + b) - (a * b) / (b % a)
    return 0


def f_binop_cold_leaves(a, b):
    for i in range(3):
        if i:
            while i:
                return (a ** b ** 2, a // b, a << b, a >> b)
    return 0


def f_binop_bitwise(a, b):
    for i in range(3):
        if i:
            while i:
                return (a & b) | (a ^ b)
    return 0


def f_binop_matmult(a, b):
    for i in range(3):
        if i:
            while i:
                return a @ b
    return 0


def f_unary_double_neg(a, b):
    for i in range(3):
        if i:
            while i:
                return -a - -b
    return 0


def f_unary_invert_uadd(a):
    for i in range(3):
        if i:
            while i:
                return ~a + (+a) + -(-a)
    return 0


def f_unary_not_chain(a, b, c):
    for i in range(3):
        if i:
            while i:
                return not a + (not b) + (not not c)
    return 0


def f_compare16_full(a, b, c, xs):
    for i in range(3):
        if i:
            while i:
                return (a == b, a != b, a < b, a <= b, a > b, a >= b,
                        a is b, a is not b, a in xs, a not in xs,
                        b == c, b != c, c < a, c <= a, c > b, c >= b)
    return 0


def f_pow_right_assoc(a):
    for i in range(3):
        if i:
            while i:
                return 2 ** 3 ** 2 + a
    return 0


def f_floor_div_shift(a, b):
    for i in range(3):
        if i:
            while i:
                return (-a) // 2 + (b << 1) + (1 << 2 << 3)
    return 0


def f_ops_in_containers(a, b, c):
    for i in range(3):
        if i:
            while i:
                return [a + b, (a - c, {a * b}, {a: b | c})]
    return 0


def f_ops_as_call_args(a, b):
    def sink(x, y):
        return x - y
    for i in range(3):
        if i:
            while i:
                return sink(a << b, a >> b)
    return 0
