"""复现 06：生成器表达式 — co_filename 元数据差异。

模式：模块含生成器表达式。genexpr 的 code 对象 co_filename 在原始为源文件路径，
反编译产物为 '<decompiled>'。字节码指令相同，co_filename 为元数据差异。
"""
result = sum(x * 2 for x in range(10))
