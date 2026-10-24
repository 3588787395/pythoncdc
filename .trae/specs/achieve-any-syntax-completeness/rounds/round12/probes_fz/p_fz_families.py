"""FZ 四族合成变体探针（Task 4.5）：4.1 starred-unpack / 4.2 send 绑定 /
4.3 posonly 签名 / 4.4 return-in-finally 内联。

每族 ≥1 变体，全部可调用（call_exprs 覆盖 R1）。族级谓词均为 I.4 白名单
（块内 opcode 序 / 异常表 / code object 结构字段），无名字/偏移特判。
"""


def fz1_unpack_after_stmt(n):
    """族 4.1：完整前导语句 + 星号解包（值段切分族——前导语句不得被吞）。"""
    data = [n, n + 1, n + 2, n + 3]
    head, *mid, tail = data
    return head + tail + len(mid)


def fz2_send_gen(n):
    """族 4.2：send 值绑定（value = yield 0 + 循环内 value = yield v+1）。"""
    log = []

    def gen(k):
        try:
            v = yield 0
            while v < k:
                v = yield v + 1
        finally:
            log.append('closed')
    g = gen(n)
    out = [next(g), g.send(1), g.send(2)]
    return out, log


def fz3_posonly(a, b=2, /, c=3, *, d=4):
    """族 4.3：posonly 前缀 + 默认值尾对齐 + kwonly（``/`` 与元数据族）。"""
    return a + b + c + d


def fz4_ret_in_fin(events):
    """族 4.4：return-in-finally 内联直落（值段 + 双层 finally 副本 + RETURN）。"""
    try:
        for i in range(3):
            try:
                if i == 0:
                    return ('hit', i)
            finally:
                events.append(('fin', i))
    finally:
        events.append('outer')
    return ('done', len(events))


def main():
    ev = []
    return [
        fz1_unpack_after_stmt(3),
        fz2_send_gen(5),
        fz3_posonly(1),
        fz4_ret_in_fin(ev),
        ev,
    ]
