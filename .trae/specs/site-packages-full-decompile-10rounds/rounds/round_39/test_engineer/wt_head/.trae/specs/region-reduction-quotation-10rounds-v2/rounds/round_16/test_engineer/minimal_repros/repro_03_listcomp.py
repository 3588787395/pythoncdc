"""复现 03：列表推导式 — co_filename 元数据差异。

模式：模块含列表推导式。listcomp 的 code 对象 co_filename 在原始为源文件路径，
反编译产物为 '<decompiled>'。字节码指令相同，co_filename 为元数据差异。
对应 build_future_fill_time 中的 listcomp code 对象（R15 已确认 listcomp 完全相等）。
"""
result = [x * 2 for x in range(10)]
