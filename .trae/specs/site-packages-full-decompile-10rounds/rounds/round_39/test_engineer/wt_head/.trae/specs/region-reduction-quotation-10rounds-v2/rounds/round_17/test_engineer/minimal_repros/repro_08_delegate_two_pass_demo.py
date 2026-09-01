"""复现 08：委托机制演示 — 两阶段比较。

模式：演示 R17 修复工程师的"传递性不一致委托"方案 A：
1. Pass 1：比较所有非 <module> 函数，建立 results dict（含 get_str_data=len_diff 等）
2. Pass 2：比较 <module>，对 LOAD_CONST code 对象查询 results dict；
   若 co_name 已在 results 中（无论 match/mismatched），视为一致（委托）

结果：<module> 的 1023 条自身指令全部正确，133 个嵌入对象全部委托 → <module> match。
一致函数数 146 → 147（+1）。

本复现演示该两阶段结构：module 调用多个函数，函数已独立定义/比较。
"""
def f1(x):
    return x

def f2(x):
    return x + 1

def f3(x):
    # 模拟 get_str_data：独立比较为 mismatched，但在 <module> 中委托
    a = str(x)
    b = a + "1"
    c = b + "2"
    d = c + "3"
    return d

# module 级引用 f1/f2/f3（通过 LOAD_CONST 嵌入 code 对象）
CALLERS = [f1, f2, f3]
