"""复现 05：集合推导式 — co_filename 元数据差异。

模式：模块含集合推导式。setcomp 的 code 对象 co_filename 在原始为源文件路径，
反编译产物为 '<decompiled>'。字节码指令相同，co_filename 为元数据差异。
"""
result = {x % 3 for x in range(20)}
