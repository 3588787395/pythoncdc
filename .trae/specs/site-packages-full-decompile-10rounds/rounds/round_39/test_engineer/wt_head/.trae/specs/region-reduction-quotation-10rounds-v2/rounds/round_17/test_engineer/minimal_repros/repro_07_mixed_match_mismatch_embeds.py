"""复现 07：混合 match/mismatched 嵌入对象 — 委托选择性生效。

模式：<module> 的 133 个嵌入对象中，130 个 match（如 obtain_date @idx441，
指令 58 vs 58 相同），3 个 mismatched。委托机制对所有已独立比较的对象一视同仁：
无论独立状态是 match 还是 mismatched，都在 <module> 中视为一致（委托）。
match 的对象委托后仍一致（无变化），mismatched 的对象委托后不再传播不一致。

关键：idx 441 (obtain_date) co_filename 不同但指令相同 → instr_equal=True；
idx 444 (get_str_data) 指令长度不同 → instr_equal=False。委托使两者在 <module>
中都被跳过。

对应：<module> @idx441 (obtain_date, match), @idx444 (get_str_data, mismatched)。
"""
def matched_a(x):
    # 模拟 obtain_date @idx441：指令相同，instr_equal=True
    return x + 1

def matched_b(y):
    return y * 2

def mismatched_c(z):
    # 模拟 get_str_data @idx444：指令长度不同
    a = str(z)
    b = a + "p"
    c = b + "q"
    d = c + "r"
    return d

def matched_d(w):
    return w - 1
