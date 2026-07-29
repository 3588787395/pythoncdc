"""复现 01：模块级嵌套函数 — co_filename 元数据差异。

模式：模块定义一个嵌套函数。原始 pyc 编译时 co_filename 为源文件路径
（如 ./fly_docker_py311/fly/data/quotation.py），反编译产物编译时
co_filename 为 '<decompiled>'。两者字节码指令完全相同，co_filename 不影响语义。

对应：<module> @idx444 (LOAD_CONST <code get_str_data>) — code 对象 co_filename 差异。
注意：实际 <module> 失败根因为 get_str_data 的 len_diff(-48)，非 co_filename；
本复现演示 co_filename 差异本身（无害的元数据差异）。
"""
def get_str_data(x):
    return str(x)
