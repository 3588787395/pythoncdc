"""复现 07：多重嵌套函数 — co_filename 元数据差异。

模式：模块定义函数，函数内再定义嵌套函数。所有 code 对象的 co_filename
在原始为源文件路径，反编译产物为 '<decompiled>'。字节码指令相同。
对应 <module> 中多个 LOAD_CONST <code ...> 指令（如 obtain_date, get_str_data 等）。
"""
def outer(a):
    def inner(b):
        return b + 1
    return inner(a)
