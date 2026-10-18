"""R2 合成变体 F3a（rv7_02 三元链式比较族 item 9 交叉变体，非语料）。"""


def r_two_tern(p, q, r, s, t, c1, c2):
    return (p if c1 else q) >= (r if c2 else s) < t


def r_three_tern(p, q, r, s, m, n, c1, c2, c3):
    return (p if c1 else q) != (r if c2 else s) <= (m if c3 else n)
