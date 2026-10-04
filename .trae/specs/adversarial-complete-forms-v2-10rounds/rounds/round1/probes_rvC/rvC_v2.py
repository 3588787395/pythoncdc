# rvC 变体2：try 体含 while 循环 + 循环内 raise（制造异常边入循环头场景）。
# 预期：while 头在 try 体内，异常表令循环头经异常边持有 finally 异常副本
# 入口（PUSH_EXC_INFO 块）作后继；副本入口的前驱含循环头但全部为异常边，
# 修复后守卫不得误判其为宿主循环出口块；finally 语句 sink.append(len(out))
# 必须保留，finally 不得蒸发。
def drain(q, limit, sink):
    out = []
    try:
        while q:
            v = q.pop()
            if v > limit:
                raise ValueError(v)
            out.append(v)
    finally:
        sink.append(len(out))
    return out
