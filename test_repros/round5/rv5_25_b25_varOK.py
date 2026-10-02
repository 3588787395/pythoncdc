# Source Generated with Decompyle++ (Python version)
# File: rv5_25_b25_var.pyc (Python 3.11)

__doc__ = 'Round5 复核变体探针：B25（lambda 默认值）修复的变体攻击。'
fd_full = lambda a, b=1, c=2, *args, d, e=5, **kw: (a, b, c, args, d, e, kw)
def fd_stmt_double():
    """函数级双默认值。"""
    f = lambda x, y=1, z=2: x + y + z
    return f(1)
def lam_in_comp_full(xs):
    """推导式内 lambda *args/**kw 带默认。"""
    return [lambda a, b=2, *args, k=3: a + b + k for x in xs]
def lam_in_comp_starkw(xs):
    """推导式内 lambda 纯 vararg/kwarg。"""
    return [lambda : (args, kw) for x in xs]
def lam_kwonly_stmt():
    """函数级 kwonly 默认。"""
    return lambda x, *, y=10, z=20: x + y + z
