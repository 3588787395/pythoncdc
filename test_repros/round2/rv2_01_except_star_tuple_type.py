# rv2_01 [REVIEW2] except* 首 handler 类型为元组捕获（B8 帧前缀剔除普适性探针）
# 焦点：except* (TypeError, ValueError): —— 帧前缀 COPY 1/BUILD_LIST 0/SWAP 2
# 之后用户段为 LOAD_GLOBAL*2 + BUILD_TUPLE 2（组合段，走 ExpressionReconstructor
# 单节点重建路径），验证剔除判据对元组类型表达式不误删、不回退 'Exception'。


def f(tag):
    out = [tag]
    try:
        raise ExceptionGroup("g", [TypeError("bad"), ValueError("v")])
    except* (TypeError, ValueError) as e:
        out.append("tv")
    except* KeyError:
        out.append("key")
    out.append("after")
    return out


def g(x, b):
    try:
        raise ExceptionGroup("g2", [OSError("io")])
    except* (OSError, RuntimeError):
        b.append("os-rt")
    b.append(x)
    return len(b)
