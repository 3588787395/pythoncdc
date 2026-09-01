# family: F3 — F3 的 2 条极简形式（去掉尾部普通赋值）
# 预期字节码模式: 两条 `or` 短路 STORE_ATTR，各带一次 JUMP_IF_TRUE_OR_POP
# 实际反编译输出: 第 2 条退化成 `b`，`return o` 变成 `return env.b`
# 关联 pyc: 同上 trade.pyc / create_trade
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

def f(o, a, b, env):
    o.x = a or env.a
    o.y = b or env.b
    return o
