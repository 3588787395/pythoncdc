# Source Generated with Decompyle++ (Python version)
# File: rv6_04_finally_deferred_double.pyc (Python 3.11)

__doc__ = """rv6_04: finally 延迟 return 跨链（B34c）——双层 try/finally 嵌套与外层 finally 覆写链变体。

对照 r6_11.w_with_in_finally / w_tryfin_with_tryfin：加深嵌套
（try→try/finally→with 与 try/finally→try/finally→return 覆写），
检验 B34c 链走查在嵌套深度增加时是否仍封闭。
"""
def try_fin_with_nested(xs, mgr):
    try:
        try:
            xs[0]
        finally:
            with mgr:
                pass
    finally:
        xs.append(1)
def double_fin_overwrite(xs):
    try:
        try:
            xs[0]
        finally:
            pass
    finally:
        return xs[1]
def try_fin_fin_body_with(xs, mgr):
    try:
        xs[0] + xs[1]
    finally:
        with mgr as m:
            xs.append(m)
