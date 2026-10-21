# Source Generated with Decompyle++ (Python version)
# File: l3_g1_r2_boolop_ternary_while.pyc (Python 3.11)

__doc__ = """L3 §3 通用性抽检 — 族 R2（条件合并块族：If / BoolOp / IfExp 的合并与短路链）。

新构型（非语料、非 B98/B123/B43/B78 设计目标）：
  BoolOp 的**左**操作数是三元（IfExp），右操作数是嵌套 and 链；
  宿主是 **while** 头条件（不是 if 体 / 推导式过滤窗）。
判据问题：B98 的「or/and 链前缀过滤 + 合并块归约」与 B123 的「and 尾 IfExp 钻石吸收」
  其触发谓词是否与「左操作数是三元」「宿主是 while 头」这一定位绑定？
"""
def r2_lt(xs, flag):
    out = []
    i = 0
    if (xs[i] if flag else -xs[i]):
        if xs[i] > 0:
            if xs[i] < 9:
                i += 1
                if flag:
                    xs[i]
                else:
                    -xs[i]
        else:
            return out
def r2_nested_and_or(a, b, c):
    """BoolOp 链中 and 与 or 交替，且链尾为三元。"""
    v = (a or b) and a
    v = b or c
    return v
