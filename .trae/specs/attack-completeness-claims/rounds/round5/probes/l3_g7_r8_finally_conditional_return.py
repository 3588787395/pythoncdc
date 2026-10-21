"""L3 §3 通用性抽检 — 族 R8（终审族：B153–B162 的 finally 归属唯一化 / 臂尾回边 / 链尾判据）。

新构型（非语料）：
  `finally` 体含**条件 return**（Python 中 finally 的 return 会吞掉异常与
  try 体的 return）；且 try 体既有 `return` 又有 `raise`。
  已落地的 B73 是「finally 体含条件段时 handler 内 return 路径上的条件段副本头
  中继块判定」、B155/B156 是「handler 臂尾 = 内联 finally 副本 + 回边跳转」。
  两者均未覆盖「finally 体内 return」这一形态。
判据问题：B155 的「臂尾回边块 = 显式 break/continue」判据与 B157 的
  「finally 归属唯一化」在 finally 体含 return 时是否仍然成立？
"""


def r8_fin_return(xs):
    for x in xs:
        try:
            if x:
                return "body"
            raise ValueError(x)
        except ValueError:
            return "handler"
        finally:
            if x < 0:
                return "finally"
    return "end"


def r8_fin_return_nested(xs):
    for x in xs:
        try:
            try:
                if x:
                    return "inner-body"
            finally:
                if x < 0:
                    return "inner-fin"
        finally:
            pass
    return "end"
