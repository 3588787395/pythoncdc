"""L3 §5 — B142（嵌套 finally 副本归属）最小复现 + 同族兄弟形。

B142 登记于 rounds/round6/FIX.md:92-93（稀窝，park 不追）；
本探针逐字复刻 adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/
v_b71_face.py 的 `v_nest_fin_continue`，并加一个同族兄弟形
（内层 finally 体含条件段 ⇒ 触发 B73「finally 体含条件段」路径）。

源语义（v_nest_fin_continue）：
  对每个 r：内层 try 体若 r==0 则 continue（内层 finally 的 out.append(1) 先执行，
  再执行外层 finally 的 out.append(2)，**内层 try 体与外层 try 体之后的
  out.append(r) 都不执行**）；r!=0 时两级 finally 各执行一次，随后 out.append(r)。
  ⇒ out.append(1) 与 out.append(2) 每个元素**各执行一次**。
"""


def v_nest_fin_continue(rows):
    out = []
    for r in rows:
        try:
            try:
                if r == 0:
                    continue
            finally:
                out.append(1)
        finally:
            out.append(2)
        out.append(r)
    return out


def v_nest_fin_continue_cond(rows):
    """同族兄弟形：内层 finally 体含条件段（触及 B73 的副本头中继判据）。"""
    out = []
    for r in rows:
        try:
            try:
                if r == 0:
                    continue
            finally:
                if r < 0:
                    out.append(-1)
                out.append(1)
        finally:
            out.append(2)
        out.append(r)
    return out
