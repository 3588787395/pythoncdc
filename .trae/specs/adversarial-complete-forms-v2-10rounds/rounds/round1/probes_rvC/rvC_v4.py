# rvC 变体4（诊断）：与变体2同形但循环内无 raise，用于刻画变体2
# finalbody 泄漏循环体镜像的触发条件（异常表边存在性 vs 循环形态本身）。
def drain_plain(q, sink):
    out = []
    try:
        while q:
            v = q.pop()
            out.append(v)
    finally:
        sink.append(len(out))
    return out
