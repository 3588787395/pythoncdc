"""复现 05：第一个嵌入不一致即导致 <module> 失败 — 短路传播。

模式：<module> 按指令顺序比较，遇到第一个不一致的嵌入 code 对象即 first_diff。
idx 444 (get_str_data) 是第一个失败点。即便后续还有 change_his_to_backward、
get_date_and_count 不一致，比较在 444 处已短路返回。

委托机制不依赖短路：所有嵌入对象（无论 match/mismatched）都委托给独立比较，
因此 <module> 的所有 LOAD_CONST code 指令都视为一致，first_diff 消失。

对应：<module> first_diff@idx444。
"""
def early_func(x):
    return x

def first_mismatch(a):
    # 模拟 get_str_data @idx444：第一个失败点
    s = str(a)
    t = s + "1"
    u = t + "2"
    return u

def later_func(b):
    return b
