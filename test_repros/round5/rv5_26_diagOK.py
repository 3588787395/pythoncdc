# Source Generated with Decompyle++ (Python version)
# File: rv5_26_diag.pyc (Python 3.11)

__doc__ = 'Round5 复核鉴别诊断：定位三个变体失败的机制归属。'
def diag_vararg_fn():
    """函数级纯 vararg/kwarg lambda（无默认值）。"""
    f = lambda : (args, kw)
    return f
def diag_nested_try_plain(xs, log):
    """嵌套 try 包 return 普通值（无推导式）。"""
    try:
        try:
            xs
        finally:
            log.append(1)
    finally:
        log.append(2)
def diag_sync_genexp_arg(xs):
    """同步 GenExp 作调用实参（对照组）。"""
    return sum((x for x in xs))
