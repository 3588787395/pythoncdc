# rv2_03 [REVIEW2] 帧前缀剔除边界探针：用户类型表达式恰为空列表字面量
# 焦点：`except* []:` 是唯一用户段以 BUILD_LIST 0 开头的形态（与帧前缀第二条
# 同签名）——剔除判据要求三条逐位全等（COPY 1 先行），验证只剔帧头三条、
# 用户 BUILD_LIST 0 原样保留（判据不被用户代码伪造/多删）。
# 注意：本探针只验证编译期形态保持（不触发运行期 raise）。


def f(tag):
    out = [tag]
    try:
        tag = tag + "x"
    except* []:
        out.append("empty-list-type")
    return out
