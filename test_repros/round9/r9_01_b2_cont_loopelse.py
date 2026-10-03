"""Round 9 B2 守卫族回归攻击 1：If×continue 守卫 × loop-else 外推。

攻击面：_block_is_continue_target（region_ast_generator.py:12243）+
_loop_else_set 排除（:12377-12381）。守卫适用形态外推一格：
continue 守卫与 for-else/while-else 的 else 块集合交叠。
"""


def cont_in_for_else(xs, c):
    for x in xs:
        if c(x):
            continue
        use(x)
    else:
        finish()
    return 1


def cont_in_while_else(a, b):
    while a:
        if b():
            continue
        a = a - 1
    else:
        pass
    return 2


def cont_then_body_after(a, b, xs):
    for x in xs:
        if b:
            continue
        x = x + 1
        keep(x)
    return 3


def cont_negated_guard(xs, a):
    for x in xs:
        if not a(x):
            use(x)
        else:
            continue
    return 4
