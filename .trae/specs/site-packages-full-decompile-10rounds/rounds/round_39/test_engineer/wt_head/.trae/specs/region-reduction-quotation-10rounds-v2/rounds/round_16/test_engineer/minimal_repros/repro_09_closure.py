"""复现 09：闭包捕获变量 — co_filename 元数据差异。

模式：模块定义闭包函数（嵌套函数捕获外层变量）。闭包 code 对象的 co_filename
在原始为源文件路径，反编译产物为 '<decompiled>'。字节码指令相同（含 LOAD_DEREF），
co_filename 为元数据差异。
"""
def make_adder(n):
    def adder(x):
        return x + n
    return adder
