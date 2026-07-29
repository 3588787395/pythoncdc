"""复现 04：模块自身指令全部正确，仅嵌入对象不一致 — 委托的核心场景。

模式：<module> 自身 1023 条指令全部正确（orig_len == new_len，逐条相等）。
所有 133 个嵌入 code 对象中，130 个 match，3 个 mismatched（已独立比较计入）。
<module> 失败纯粹是传递性的：嵌入的不一致函数导致递归比较失败。
委托机制：嵌入对象已独立比较，<module> 中不再重复比较 → <module> 变为 match。

对应：诊断证据 <module> orig_len=1023 new_len=1023 (diff=+0)，133 嵌入对象中
130 match + 3 mismatched。
"""
def matched_func_1(x):
    return x + 1

def matched_func_2(y):
    return y * 2

def mismatched_func(z):
    # 模拟 get_str_data：len_diff（反编译丢失指令）
    a = str(z)
    b = a + "x"
    c = b + "y"
    return c
