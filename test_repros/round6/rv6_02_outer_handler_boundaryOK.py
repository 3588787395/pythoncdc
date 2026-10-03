# Source Generated with Decompyle++ (Python version)
# File: rv6_02_outer_handler_boundary.pyc (Python 3.11)

__doc__ = """rv6_02: with 清理块 + 外部 WITH_EXCEPT_START 处理器相邻（B34b 统一判据可达性边界的反例变体）。

对照 r6_10.w_loop_nest_with：改宿主结构（while 代替 for、双层 with 内层
早退 + 外层尾部显式 return None），检验内层 with 的 cleanup 位置扫描
不可沿外部 WITH_EXCEPT_START 处理器越界收编外层协议链/函数尾 exit-block。
"""
def inner_with_outer_tail(mgr, xs):
    with mgr:
        while xs:
            with mgr as y:
                if y:
                    return y
            xs = xs[1:]
    return None
def outer_raise_catch(m1, m2, v):
    with m1, m2:
        if v:
            raise ValueError(v)
    return 1
def nested_with_else_loop(mgr, xs):
    out = 0
    for x in xs:
        with mgr:
            if x:
                out += x
                while False:
                    pass
    else:
        out -= 1
    return out
