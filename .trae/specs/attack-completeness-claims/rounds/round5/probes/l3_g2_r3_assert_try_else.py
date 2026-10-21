"""L3 §3 通用性抽检 — 族 R3（try / raise / assert 宿主族）。

新构型（非语料）：
  `assert` 位于 **try 的 else 子句**（已落地的 B135 是 IfRegion→Assert，
  B146/B147 是 with 体内 assert；try-else 内的 assert 是新的宿主位置）；
  同时 `raise ... from ...` 出现在 handler 内。
判据问题：B135「IfRegion → ast.Assert」的触发谓词是否覆盖「assert 位于 try-else 体」
  这一新宿主，还是仅识别「if 臂退化为 assert」形态？
"""


def r3_assert_else(xs):
    out = []
    for x in xs:
        try:
            out.append(x)
        except ValueError:
            out.append(0)
        else:
            assert x >= 0, "neg"
            out.append(x)
    return out


def r3_raise_from(xs):
    out = []
    for x in xs:
        try:
            if x < 0:
                raise KeyError(x)
        except KeyError:
            raise ValueError("bad") from None
        out.append(x)
    return out
