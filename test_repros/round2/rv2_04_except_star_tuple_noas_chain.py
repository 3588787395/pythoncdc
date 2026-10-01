# rv2_04 [REVIEW2] 链式 except* 第二 handler 丢失面的变体隔离（残留登记辅助）
# 焦点：首 handler 元组类型但无 as 绑定，第二 handler 简单名——隔离
# rv2_01.f 残留（第二 handler 退化为 if <类型> is not None）的触发变量
# 是「元组类型」还是「as 绑定」。基线 fe486d42 同读数对照。


def f(tag):
    out = [tag]
    try:
        raise ExceptionGroup("g", [TypeError("bad"), ValueError("v")])
    except* (TypeError, ValueError):
        out.append("tv")
    except* KeyError:
        out.append("key")
    out.append("after")
    return out
