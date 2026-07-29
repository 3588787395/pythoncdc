"""复现 04：字典推导式 — co_filename 元数据差异。

模式：模块含字典推导式。dictcomp 的 code 对象 co_filename 在原始为源文件路径，
反编译产物为 '<decompiled>'。字节码指令相同，co_filename 为元数据差异。
"""
result = {k: v for k, v in enumerate(range(10))}
