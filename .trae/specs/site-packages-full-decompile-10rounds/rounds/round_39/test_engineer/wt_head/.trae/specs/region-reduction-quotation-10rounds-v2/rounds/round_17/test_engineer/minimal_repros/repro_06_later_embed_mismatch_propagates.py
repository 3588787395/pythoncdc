"""复现 06：后续嵌入不一致也会传播 — 非仅首个失败点。

模式：若 get_str_data 被归一化（假设修复），<module> 仍会在 @idx453
(change_his_to_backward, instr_diff) 和 @idx495 (get_date_and_count, len_diff)
处失败。即 <module> 的失败是多个 deferred 函数传递性不一致的叠加。

委托机制一次性委托所有已独立比较的嵌入对象，覆盖全部 3 个 mismatched 函数，
使 <module> 彻底变为 match。

对应：<module> @idx453 (change_his_to_backward), @idx495 (get_date_and_count)。
"""
def func_ok(x):
    return x

def func_len_diff(a):
    # 模拟 change_his_to_backward 之后的 get_date_and_count (len_diff -27)
    total = 0
    for i in range(10):
        total += i
    return total

def func_instr_diff(b):
    # 模拟 change_his_to_backward (instr_diff)
    res = []
    if b:
        res.append(b)
    return res
