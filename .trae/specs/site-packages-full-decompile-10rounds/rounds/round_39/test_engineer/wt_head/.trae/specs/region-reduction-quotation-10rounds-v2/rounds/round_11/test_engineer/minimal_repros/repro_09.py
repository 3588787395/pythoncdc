"""repro_09: <module> 嵌套 code 对象 co_filename 元数据差异
区域类型: Module
违反原则: 4 (入口引用语义 — co_filename 引用语义)
对应函数: <module>
缺陷镜像: 嵌套 code 对象(如 one_prod_to_dataframe)的 co_filename 原始为
  `./fly_docker_py311/fly/data/quotation.py`，反编译产物为 `<decompiled>`，
  模块层 LOAD_CONST 的 code 对象 repr 在 idx 394 处不一致(co_filename 引用语义未对齐)。
  diff_detail idx 394: orig LOAD_CONST <code ... file "./fly_docker_py311/.../quotation.py">
  vs new LOAD_CONST <code ... file "<decompiled>">。
"""


def one_prod_to_dataframe(x):
    return x


def build_future_fill_time(t):
    return t
