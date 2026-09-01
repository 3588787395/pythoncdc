"""复现 03：模块嵌入多个不一致函数 — 传递性叠加。

模式：<module> 嵌入 get_str_data(len_diff)、change_his_to_backward(instr_diff)、
get_date_and_count(len_diff) 三个不一致的 code 对象。
<module> 在第一个不一致的嵌入对象（get_str_data @idx444）处即失败。
即使归一化第一个，还会在 @idx453、@idx495 处失败。
传递性委托机制将这三个嵌入对象的一致性委托给其独立比较，使 <module> 变为 match。

对应：<module> @idx444/453/495。
"""
def func_a(x):
    # 模拟 get_str_data (len_diff)
    a = str(x)
    b = a.strip()
    return b

def func_b(y):
    # 模拟 change_his_to_backward (instr_diff)
    out = []
    for v in y:
        if v:
            out.append(v)
    return out

def func_c(z):
    # 模拟 get_date_and_count (len_diff)
    count = 0
    for i in range(len(z)):
        count += 1
    return count
