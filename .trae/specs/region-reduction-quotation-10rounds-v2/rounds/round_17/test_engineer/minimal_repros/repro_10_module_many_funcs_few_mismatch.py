"""复现 10：模块嵌入大量函数，仅少数不一致 — 真实 quotation.pyc 缩影。

模式：模拟 quotation.pyc 的真实结构：<module> 嵌入 133 个顶层函数 code 对象，
其中 130 个 match，3 个 mismatched（get_str_data/change_his_to_backward/get_date_and_count）。
<module> 自身 1023 条指令全部正确。委托机制使 <module> 的所有嵌入对象委托给独立比较，
<module> 从 instr_diff@444 变为 match，一致函数数 146 → 147。

本复现用 6 个函数缩影演示（5 match + 1 mismatched）。
"""
def m1(x):
    return x

def m2(x):
    return x + 1

def m3(x):
    return x * 2

def m4(x):
    return x - 1

def m5(x):
    return x ** 2

def mismatched(x):
    # 模拟 get_str_data：独立比较 mismatched，<module> 中委托
    a = str(x)
    b = a + "1"
    c = b + "2"
    d = c + "3"
    e = d + "4"
    return e

REGISTRY = [m1, m2, m3, m4, m5, mismatched]
