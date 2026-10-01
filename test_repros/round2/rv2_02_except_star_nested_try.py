# rv2_02 [REVIEW2] except* 嵌在 try 嵌套内层（B8 帧前缀剔除普适性探针）
# 焦点：外层普通 try/except 包裹内层 try/except* —— 内层 except* 首 handler
# 的帧（PUSH_EXC_INFO + COPY 1/BUILD_LIST 0/SWAP 2 + 类型表达式 + CHECK_EG_MATCH）
# 处于嵌套异常表下，验证剔除判据在嵌套帧布局下仍逐位锚定末个 PUSH_EXC_INFO。


def f(tag):
    out = []
    try:
        try:
            raise ExceptionGroup("inner", [TypeError("t")])
        except* TypeError:
            out.append("star")
    except ValueError:
        out.append("plain")
    return out


def g(a, b):
    try:
        if a:
            try:
                raise ExceptionGroup("g2", [KeyError("k")])
            except* KeyError as e:
                b.append("k")
            except* (TypeError, ValueError):
                b.append("tv")
    except OSError:
        b.append("os")
    return b
