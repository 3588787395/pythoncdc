# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b43tail_b.pyc (Python 3.11)

__doc__ = 'R2 合成变体 F8b（B43 链式比较 and 尾操作数族 item 15 交叉变体·镜像序，非语料）。'
def m_lead_flag(flag, a, b, c):
    return flag and a < b < c
def m_mixed_ops(a, b, c, d):
    return a <= b != c and d
def m_two_chains(a, b, c, x, y, z):
    return a < b < c and x < y < z
