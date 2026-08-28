# family: F1 — <call>().attr = value — STORE_ATTR 的值被丢弃变成 None
# 预期字节码模式: LOAD_CONST <value>; PUSH_NULL; LOAD_NAME f; PRECALL; CALL; STORE_ATTR x
# 实际反编译输出: f().x = None   （值 5 丢失）
# 关联 pyc: site-packages/IQEngine/plugins/plugin_system_accounts/api/api_stock.pyc  <module>  baseline first_diff idx=111: LOAD_CONST 10 -> LOAD_CONST None
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

def f():
    return object()


f().x = 5
