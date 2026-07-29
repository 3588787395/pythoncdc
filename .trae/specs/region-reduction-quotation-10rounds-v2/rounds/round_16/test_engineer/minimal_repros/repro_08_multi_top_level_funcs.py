"""复现 08：多顶层函数模块 — co_filename 元数据差异（最贴近 <module> 场景）。

模式：模块定义多个顶层函数（模拟 quotation.py 的 <module>）。
每个函数的 code 对象 co_filename 在原始为源文件路径，反编译产物为 '<decompiled>'。
<module> 的 LOAD_CONST 指令加载每个函数的 code 对象，co_filename 差异为元数据差异。
"""
def obtain_date():
    return 1

def get_str_data():
    return 2

def change_his_to_backward():
    return 3
