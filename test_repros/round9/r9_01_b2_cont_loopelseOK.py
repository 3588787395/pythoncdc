# Source Generated with Decompyle++ (Python version)
# File: r9_01_b2_cont_loopelse.pyc (Python 3.11)

__doc__ = """Round 9 B2 守卫族回归攻击 1：If×continue 守卫 × loop-else 外推。

攻击面：_block_is_continue_target（region_ast_generator.py:12243）+
_loop_else_set 排除（:12377-12381）。守卫适用形态外推一格：
continue 守卫与 for-else/while-else 的 else 块集合交叠。
"""
def cont_in_for_else(xs, c):
    for x in xs:
        if c(x):
            continue
        use(x)
        continue
    finish()
    return 1
def cont_in_while_else(a, b):
    while a:
        if b():
            continue
        a = a - 1
    return 2
def cont_then_body_after(a, b, xs):
    for x in xs:
        if b:
            continue
        x = x + 1
        keep(x)
        continue
    return 3
def cont_negated_guard(xs, a):
    for x in xs:
        if not a(x):
            use(x)
            continue
    return 4
