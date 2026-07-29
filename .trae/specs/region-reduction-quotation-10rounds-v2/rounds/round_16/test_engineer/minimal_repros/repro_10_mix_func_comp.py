"""复现 10：推导式 + 函数混合 — co_filename 元数据差异。

模式：模块同时含函数定义和推导式，多种 code 对象共存。
所有 code 对象的 co_filename 在原始为源文件路径，反编译产物为 '<decompiled>'。
字节码指令相同，co_filename 为元数据差异，不影响字节码语义。
"""
def process(items):
    return [item for item in items if item > 0]

VALUES = [x for x in range(5)]
